"""Tests for agent initialization."""
from unittest.mock import patch


class TestAgentImports:
    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_research_agent_init(self, mock_llm):
        from src.agents.research_agent import ResearchAgent
        agent = ResearchAgent()
        assert agent.name == "Deep Research Agent"
        assert len(agent.tools) == 1

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_blog_writer_init(self, mock_llm):
        from src.agents.blog_writer import BlogWriterAgent
        agent = BlogWriterAgent()
        assert agent.name == "SEO Blog Writer Agent"
        assert len(agent.tools) == 1

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_linkedin_writer_init(self, mock_llm):
        from src.agents.linkedin_writer import LinkedInWriterAgent
        agent = LinkedInWriterAgent()
        assert agent.name == "LinkedIn Post Writer Agent"
        assert agent.tools == []

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_image_agent_init(self, mock_llm):
        from src.agents.image_agent import ImageAgent
        agent = ImageAgent()
        assert agent.name == "Image Generation Agent"
        assert len(agent.tools) == 1

    @patch("src.agents.base_agent.ChatGoogleGenerativeAI")
    def test_content_strategist_init(self, mock_llm):
        from src.agents.content_strategist import ContentStrategistAgent
        agent = ContentStrategistAgent()
        assert agent.name == "Content Strategist Agent"
        assert agent.tools == []
