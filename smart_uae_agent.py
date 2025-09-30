"""
Smart UAE Tourism Assistant - LangChain Multi-Tool Agent
A comprehensive AI assistant for UAE tourism information and trip planning.
"""

import os
import sys
from typing import List, Optional
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# Import custom tools
from uae_tools import UAEKnowledgeSearchTool, PrayerTimeTool, TripBudgetPlanner


class SmartUAEAgent:
    """Main class for the Smart UAE Tourism Assistant"""
    
    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the Smart UAE Agent
        
        Args:
            llm_provider: Choice of LLM provider ('openai', 'gemini', or 'groq')
        """
        load_dotenv()
        
        self.llm_provider = llm_provider
        self.llm = self._initialize_llm()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key='input',
            output_key='output'
        )
        self.tools = self._initialize_tools()
        self.agent_executor = self._create_agent()
    
    def _initialize_llm(self):
        """Initialize the chosen LLM"""
        if self.llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
                api_key=api_key
            )
        
        elif self.llm_provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            return ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.7,
                google_api_key=api_key
            )
        
        elif self.llm_provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            return ChatGroq(
                model="mixtral-8x7b-32768",
                temperature=0.7,
                groq_api_key=api_key
            )
        
        else:
            raise ValueError("LLM provider must be 'openai', 'gemini', or 'groq'")
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize all available tools"""
        return [
            UAEKnowledgeSearchTool(),
            PrayerTimeTool(),
            TripBudgetPlanner()
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent with tools and memory"""
        
        # Custom prompt template for UAE tourism assistant
        template = """You are a helpful and knowledgeable UAE Tourism Assistant. Your role is to help tourists plan their trips to the United Arab Emirates by providing accurate information, recommendations, and practical advice.

INSTRUCTIONS:
1. Use the available tools to search for factual information about UAE cities, attractions, prayer times, and budget calculations
2. For trip planning and recommendations, use your knowledge to create detailed, day-by-day itineraries
3. Always be friendly, helpful, and culturally sensitive
4. Provide practical tips and insider knowledge when relevant
5. If you don't have specific information, use the tools available to search for it
6. Format your responses clearly with headers, bullet points, and structured information

AVAILABLE TOOLS:
{tools}

TOOL NAMES: {tool_names}

CONVERSATION HISTORY:
{chat_history}

USER INPUT: {input}

THOUGHT PROCESS:
Think step by step about how to help the user. Consider:
- What information do they need?
- Which tools should I use?
- What recommendations can I provide?
- How can I make this response most helpful?

{agent_scratchpad}
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["tools", "tool_names", "chat_history", "input", "agent_scratchpad"]
        )
        
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor with memory
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=False
        )
        
        return agent_executor
    
    def chat(self, user_input: str) -> str:
        """
        Main chat interface for the agent
        
        Args:
            user_input: User's question or request
            
        Returns:
            Agent's response
        """
        try:
            # Check if this is a trip planning request that should use LLM directly
            if self._is_trip_planning_request(user_input):
                return self._generate_trip_recommendation(user_input)
            
            # Otherwise, use the agent with tools
            response = self.agent_executor.invoke({"input": user_input})
            return response["output"]
            
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            print(f"Error in chat: {e}")
            return error_msg
    
    def _is_trip_planning_request(self, user_input: str) -> bool:
        """Check if the request is for trip planning/recommendations"""
        trip_keywords = [
            "plan my trip", "itinerary", "what can i do", "things to do",
            "day trip", "visit in", "plan for", "travel plan", "schedule",
            "recommend", "suggestion", "day by day"
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in trip_keywords)
    
    def _generate_trip_recommendation(self, user_input: str) -> str:
        """Generate LLM-based trip recommendations"""
        try:
            # First, get relevant information using tools if needed
            context = ""
            
            # Extract city name if mentioned
            cities = ["dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "fujairah", "umm al quwain"]
            mentioned_city = None
            
            for city in cities:
                if city in user_input.lower():
                    mentioned_city = city
                    break
            
            # Get city information if a city is mentioned
            if mentioned_city:
                knowledge_tool = UAEKnowledgeSearchTool()
                city_info = knowledge_tool._run(f"attractions in {mentioned_city}")
                context += f"\nCITY INFORMATION:\n{city_info}\n"
            
            # Enhanced prompt for trip recommendations
            recommendation_prompt = f"""
As a UAE Tourism Expert, create a detailed trip recommendation for the following request:

USER REQUEST: {user_input}

{context}

Please provide a comprehensive response that includes:
1. A welcoming introduction
2. Specific day-by-day itinerary (if duration is mentioned)
3. Must-visit attractions with brief descriptions
4. Practical tips (best times to visit, dress code, etc.)
5. Transportation suggestions
6. Dining recommendations
7. Cultural considerations
8. Budget tips if relevant

Make the response engaging, informative, and practical. Use bullet points and clear formatting.
Ensure all recommendations are accurate and culturally appropriate for the UAE.
"""

            # Generate recommendation using the LLM directly
            response = self.llm.invoke(recommendation_prompt)
            return response.content
            
        except Exception as e:
            print(f"Error generating trip recommendation: {e}")
            return "I'd be happy to help you plan your UAE trip! Could you provide more details about which city you'd like to visit and how many days you're planning to stay?"
    
    def get_conversation_history(self) -> str:
        """Get the current conversation history"""
        return str(self.memory.chat_memory.messages)
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear()


def main():
    """Main function for CLI interaction"""
    print("=" * 60)
    print("🇦🇪 Welcome to the Smart UAE Tourism Assistant! 🇦🇪")
    print("=" * 60)
    print("I'm here to help you plan your perfect UAE adventure!")
    print("Ask me about:")
    print("• Tourist attractions and activities")
    print("• Prayer times for UAE cities")
    print("• Trip budget planning")
    print("• Cultural tips and etiquette")
    print("• Personalized itineraries")
    print("\nType 'quit' to exit, 'clear' to clear conversation history")
    print("-" * 60)
    
    # Initialize agent
    try:
        # Try to get LLM provider from environment or use default
        llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        agent = SmartUAEAgent(llm_provider=llm_provider)
        print(f"✅ Agent initialized with {llm_provider.upper()} LLM")
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        print("Please check your API keys in the .env file")
        return
    
    # Chat loop
    while True:
        try:
            user_input = input("\n🤖 Ask me anything about UAE tourism: ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Thank you for using the Smart UAE Tourism Assistant! Have a wonderful trip to the UAE! 🌟")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_memory()
                print("✅ Conversation history cleared!")
                continue
            
            if not user_input.strip():
                continue
            
            print("\n🔍 Processing your request...")
            response = agent.chat(user_input)
            print(f"\n✈️ UAE Tourism Assistant:\n{response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! Safe travels! 🌟")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again or restart the assistant.")


if __name__ == "__main__":
    main()