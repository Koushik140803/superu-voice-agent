from vocode.streaming.models.agent import AgentConfig, AgentType

class GroqAgentConfig(AgentConfig, type=AgentType.LLM.value):  
    pass
