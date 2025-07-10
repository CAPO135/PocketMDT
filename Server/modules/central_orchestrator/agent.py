import openai
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import json

load_dotenv()  # Load environment variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the dynamic agent loader
from .agent_loader import AgentLoader

class CentralOrchestratorAgent:
    def __init__(self, model_name="gpt-4", temperature=0, config_path: str = "config/agent_registry.json"):
        self.model_name = model_name
        self.embedding_model = "text-embedding-ada-002"
        self.max_attempts = 3
        self.conversation_history = []
        
        # Validate OpenAI API key
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize dynamic agent loader
        self.agent_loader = AgentLoader(config_path)
        
        # Initialize configuration issues tracking
        self._configuration_issues = []
        
        # Load all enabled agents
        self._load_agents()

    def _load_agents(self):
        """Load all enabled agents from configuration"""
        try:
            loaded_agents = self.agent_loader.load_all_enabled_agents()
            if not loaded_agents:
                logger.warning("No enabled agents found in configuration")
                self._configuration_issues = ["No enabled agents configured"]
            else:
                logger.info(f"Successfully loaded {len(loaded_agents)} agents from configuration")
                self._configuration_issues = []
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
            self._configuration_issues = [f"Configuration loading error: {str(e)}"]

    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return issues if any"""
        issues = []
        enabled_agents = self.agent_loader.get_enabled_agents()
        
        if not enabled_agents:
            issues.append("No enabled agents found in configuration")
        
        # Check for summary agent
        summary_agent_name = self.agent_loader.get_summary_agent_name()
        summary_agents = [name for name, config in enabled_agents.items() 
                         if config.get("is_summary_agent", False)]
        
        if not summary_agents:
            issues.append("No summary agent configured")
        elif len(summary_agents) > 1:
            issues.append(f"Multiple summary agents found: {summary_agents}")
        
        # Validate each agent can be loaded
        failed_agents = []
        for name, config in enabled_agents.items():
            try:
                agent_class = self.agent_loader.load_agent_class(name)
                if not agent_class:
                    failed_agents.append(name)
            except Exception as e:
                failed_agents.append(f"{name} ({str(e)})")
        
        if failed_agents:
            issues.append(f"Failed to load agents: {', '.join(failed_agents)}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "enabled_agents": list(enabled_agents.keys()),
            "summary_agent": summary_agents[0] if summary_agents else None
        }

    def _get_configuration_help_message(self, validation_result: Dict[str, Any]) -> str:
        """Generate helpful message about configuration issues"""
        issues = validation_result["issues"]
        enabled_agents = validation_result["enabled_agents"]
        
        if not issues:
            return "Configuration is valid"
        
        message = "Configuration issues detected:\n\n"
        
        for issue in issues:
            message += f"• {issue}\n"
        
        message += "\nTo fix these issues:\n"
        message += "1. Use the agent manager CLI to add agents: python utils/agent_manager.py add <name> <module_path> <class_name>\n"
        message += "2. Enable agents: python utils/agent_manager.py enable <name>\n"
        message += "3. Set a summary agent: Update the configuration to mark one agent as 'is_summary_agent': true\n"
        message += "4. Validate configuration: python utils/agent_manager.py validate\n\n"
        
        if enabled_agents:
            message += f"Currently enabled agents: {', '.join(enabled_agents)}\n"
        else:
            message += "No agents are currently enabled.\n"
        
        return message

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((openai.APIError, openai.RateLimitError))
    )
    def get_embedding(self, text: str) -> List[float]:
        """Fetch embedding vector for a given text using OpenAI Embedding API"""
        try:
            response = self.openai_client.embeddings.create(
                input=[text],
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def generate_follow_up_questions(self, user_input: str, available_agents: List[str]) -> List[str]:
        """Generate specific follow-up questions based on available agents and user input"""
        try:
            prompt = f"""
Based on the user's input: "{user_input}"

And the available medical specialists: {', '.join(available_agents)}

Generate 3-5 specific follow-up questions that would help clarify which medical domain the user needs help with. 
Focus on symptoms, test results, or specific health concerns that would indicate which specialist is most relevant.

Format as a JSON array of strings.
"""
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a medical triage assistant helping to route patients to appropriate specialists."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            if content:
                try:
                    questions = json.loads(content)
                    if isinstance(questions, list):
                        return questions[:5]  # Limit to 5 questions
                except json.JSONDecodeError:
                    pass  # Fall through to default questions
            
            # Fallback if JSON parsing fails or content is None
            return [
                "What specific symptoms are you experiencing?",
                "Do you have any recent test results or lab work?",
                "Which part of your health are you most concerned about?",
                "Are you taking any medications currently?",
                "What prompted you to seek medical advice today?"
            ]
                
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            return [
                "What specific symptoms are you experiencing?",
                "Do you have any recent test results or lab work?",
                "Which part of your health are you most concerned about?"
            ]

    def route_request_with_embeddings(self, user_input: str, context: dict) -> Tuple[List[str], float]:
        """Determine most relevant agent(s) using semantic matching"""
        user_input_lower = user_input.lower()
        available_agents = list(self.agent_loader.get_enabled_agents().keys())
        
        # Remove SummaryAgent from routing consideration
        summary_agent_name = self.agent_loader.get_summary_agent_name()
        available_agents = [agent for agent in available_agents if agent != summary_agent_name]

        # Full report logic
        if "full report" in user_input_lower or "health summary" in user_input_lower:
            return available_agents, 1.0

        # Check for general questions that might be better handled by GeneralistAgent
        general_question_keywords = [
            "what does this mean", "explain", "help me understand", "overview", 
            "general", "what is", "tell me about", "how do i read", "interpret",
            "what are", "can you explain", "i don't understand", "confused"
        ]
        
        is_general_question = any(keyword in user_input_lower for keyword in general_question_keywords)
        
        # Generate user input embedding
        try:
            user_vector = self.get_embedding(user_input)
            similarities = []

            for agent_name in available_agents:
                description = self.agent_loader.get_agent_description(agent_name)
                if not description:
                    continue

                agent_vector = self.get_embedding(description)
                score = self.cosine_similarity(np.array(user_vector), np.array(agent_vector))
                similarities.append((agent_name, score))

            similarities.sort(key=lambda x: x[1], reverse=True)
            top_agent, top_score = similarities[0] if similarities else (None, 0)

            # If it's a general question and no specialist has high confidence, prefer GeneralistAgent
            if is_general_question and top_score < 0.8:
                generalist_score = next((score for name, score in similarities if name == "GeneralistAgent"), 0.0)
                generalist_threshold = self.agent_loader.get_generalist_confidence_threshold()
                if generalist_score > generalist_threshold:
                    return ["GeneralistAgent"], generalist_score

            return [top_agent] if top_score > 0.75 and top_agent is not None else [], top_score
            
        except Exception as e:
            logger.error(f"Error in semantic routing: {e}")
            return [], 0.0

    def create_context(self, user_input: str, document_context: str = "", conversation_history: Optional[List[Dict]] = None) -> dict:
        """Create a standardized context object for agents"""
        return {
            "user_input": user_input,
            "document_context": document_context,
            "conversation_history": conversation_history if conversation_history is not None else [],
            "timestamp": datetime.now().isoformat(),
            "agent_registry": self.agent_loader.load_all_enabled_agents()
        }

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def orchestrate(self, user_input: str, document_context: str = "", conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Main orchestration method that routes requests and manages agent execution
        
        Args:
            user_input: The user's question or request
            document_context: Document content from vector store for context
            conversation_history: Previous conversation turns
            
        Returns:
            Dict containing either agent results or clarification request
        """
        # Validate configuration first
        validation_result = self._validate_configuration()
        if not validation_result["valid"]:
            help_message = self._get_configuration_help_message(validation_result)
            return {
                "status": "configuration_error",
                "message": (
                    "I'm unable to process your request due to configuration issues with the medical specialist agents. "
                    "Please contact the system administrator to resolve these issues."
                ),
                "configuration_issues": validation_result["issues"],
                "help_message": help_message,
                "available_agents": validation_result["enabled_agents"]
            }
        
        # Create context
        context = self.create_context(user_input, document_context, conversation_history)
        
        # Route request to appropriate agents
        agents_to_run, confidence_score = self.route_request_with_embeddings(user_input, context)
        
        # Store conversation turn
        self.conversation_history.append({
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            "routed_agents": agents_to_run,
            "confidence_score": confidence_score
        })

        # Handle low confidence scenarios - use GeneralistAgent as fallback
        confidence_threshold = self.agent_loader.get_confidence_threshold()
        if not agents_to_run or confidence_score < confidence_threshold:
            # Try to use GeneralistAgent as fallback
            generalist_agent_name = "GeneralistAgent"
            generalist_agent_class = self.agent_loader.load_agent_class(generalist_agent_name)
            
            if generalist_agent_class:
                try:
                    generalist_agent = generalist_agent_class()
                    generalist_result = generalist_agent.run(context)
                    
                    return {
                        "status": "success",
                        "summary": generalist_result,
                        "agent_results": {
                            generalist_agent_name: {
                                "status": "success",
                                "output": generalist_result,
                                "timestamp": datetime.now().isoformat()
                            }
                        },
                        "confidence_score": confidence_score,
                        "routed_agents": [generalist_agent_name],
                        "fallback_used": True,
                        "message": "I've provided a general analysis of your question based on the available medical information."
                    }
                except Exception as e:
                    logger.error(f"Error running GeneralistAgent: {e}")
                    # Fall back to clarification if GeneralistAgent fails
                    pass
            
            # If GeneralistAgent is not available or fails, fall back to clarification
            available_agents = [name for name in self.agent_loader.get_enabled_agents().keys() 
                              if name != self.agent_loader.get_summary_agent_name()]
            follow_up_questions = self.generate_follow_up_questions(user_input, available_agents)
            
            return {
                "clarification_required": True,
                "confidence_score": confidence_score,
                "message": (
                    "I wasn't able to confidently identify which medical specialist would be most helpful for your concern. "
                    "Could you please provide more details about your symptoms or health issue?"
                ),
                "follow_up_questions": follow_up_questions,
                "available_specialists": available_agents
            }

        # Execute selected agents
        results = {}
        failed_agents = []
        
        for agent_name in agents_to_run:
            try:
                agent_class = self.agent_loader.load_agent_class(agent_name)
                if agent_class:
                    agent = agent_class()
                    agent_result = agent.run(context)
                    results[agent_name] = {
                        "status": "success",
                        "output": agent_result,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    failed_agents.append(agent_name)
                    
            except Exception as e:
                logger.error(f"Error running agent {agent_name}: {e}")
                failed_agents.append(agent_name)
                results[agent_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        # Generate summary if we have successful results
        if results and any(r.get("status") == "success" for r in results.values()):
            try:
                summary_agent_name = self.agent_loader.get_summary_agent_name()
                summary_agent_class = self.agent_loader.load_agent_class(summary_agent_name)
                if summary_agent_class:
                    summary_agent = summary_agent_class()
                    # Filter only successful results for summary
                    successful_results = {
                        name: result["output"] 
                        for name, result in results.items() 
                        if result.get("status") == "success"
                    }
                    
                    summary = summary_agent.summarize(successful_results, context)
                    
                    return {
                        "status": "success",
                        "summary": summary,
                        "agent_results": results,
                        "confidence_score": confidence_score,
                        "routed_agents": agents_to_run,
                        "failed_agents": failed_agents
                    }
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                return {
                    "status": "partial_success",
                    "agent_results": results,
                    "summary_error": str(e),
                    "confidence_score": confidence_score,
                    "routed_agents": agents_to_run,
                    "failed_agents": failed_agents
                }

        # If no successful results, return error
        return {
            "status": "error",
            "message": "All selected agents failed to process your request",
            "failed_agents": failed_agents,
            "confidence_score": confidence_score
        }

    def add_agent(self, name: str, agent_class: type, description: str):
        """Dynamically add a new agent to the registry"""
        self.agent_loader.add_agent_config(name, {
            "module_path": f"{agent_class.__module__}",
            "class_name": agent_class.__name__,
            "description": description,
            "enabled": True,
            "priority": 1,
            "tags": []
        })
        logger.info(f"Added new agent: {name}")

    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history"""
        return self.conversation_history.copy()

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get current configuration status and any issues"""
        validation_result = self._validate_configuration()
        return {
            "valid": validation_result["valid"],
            "issues": validation_result["issues"],
            "enabled_agents": validation_result["enabled_agents"],
            "summary_agent": validation_result["summary_agent"],
            "help_message": self._get_configuration_help_message(validation_result) if not validation_result["valid"] else None
        }

    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
