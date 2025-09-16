from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import openai
from ..config import settings

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, max_tokens: int = 500, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_resume_summary(self, profile: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def generate_resume_bullets(self, experience: Dict[str, Any]) -> List[str]:
        pass
    
    @abstractmethod
    async def tailor_resume_to_job(self, resume_content: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        pass

class OpenAIProvider(AIProvider):
    """OpenAI implementation of AI provider"""
    
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_text(self, prompt: str, max_tokens: int = 500, **kwargs) -> str:
        """Generate text using OpenAI GPT"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=kwargs.get("temperature", 0.7),
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_resume_summary(self, profile: Dict[str, Any]) -> str:
        """Generate a professional resume summary"""
        prompt = f"""
        Create a professional resume summary (2-3 sentences) for an internship candidate with the following profile:
        
        Name: {profile.get('name', 'Student')}
        Education Level: {profile.get('education_level', 'Undergraduate')}
        Skills: {', '.join(profile.get('skills', []))}
        Interests: {', '.join(profile.get('interests', []))}
        Location: {profile.get('location', 'Not specified')}
        
        The summary should be:
        - Professional and concise
        - Highlight relevant skills and interests
        - Suitable for internship applications
        - Written in third person
        """
        
        return await self.generate_text(prompt, max_tokens=150)
    
    async def generate_resume_bullets(self, experience: Dict[str, Any]) -> List[str]:
        """Generate resume bullet points for an experience"""
        prompt = f"""
        Create 3-4 professional resume bullet points for the following experience:
        
        Position: {experience.get('title', 'Position')}
        Company: {experience.get('company', 'Company')}
        Description: {experience.get('description', 'No description provided')}
        Skills Used: {', '.join(experience.get('skills', []))}
        
        Each bullet point should:
        - Start with a strong action verb
        - Include quantifiable results where possible
        - Be concise (1-2 lines max)
        - Use past tense
        - Be relevant for internship applications
        
        Return only the bullet points, one per line, starting with "•"
        """
        
        response = await self.generate_text(prompt, max_tokens=300)
        bullets = [line.strip() for line in response.split('\n') if line.strip() and line.strip().startswith('•')]
        return bullets[:4]  # Limit to 4 bullets
    
    async def tailor_resume_to_job(self, resume_content: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Tailor resume content to match a specific job description"""
        # Extract key skills and requirements from job description
        skills_prompt = f"""
        Extract the top 5 most important skills and requirements from this internship job description:
        
        {job_description[:1000]}  # Limit length
        
        Return only a comma-separated list of skills/requirements.
        """
        
        key_skills = await self.generate_text(skills_prompt, max_tokens=100)
        
        # Tailor the summary
        summary_prompt = f"""
        Rewrite this resume summary to better match the internship requirements:
        
        Original Summary: {resume_content.get('summary', '')}
        Key Job Requirements: {key_skills}
        
        Make the summary more relevant while keeping it professional and truthful.
        """
        
        tailored_summary = await self.generate_text(summary_prompt, max_tokens=150)
        
        # Create tailored version
        tailored_content = resume_content.copy()
        tailored_content['summary'] = tailored_summary
        tailored_content['_tailored_for'] = key_skills
        
        return tailored_content

class MockAIProvider(AIProvider):
    """Mock AI provider for testing/development"""
    
    async def generate_text(self, prompt: str, max_tokens: int = 500, **kwargs) -> str:
        return "This is a mock AI response for development purposes."
    
    async def generate_resume_summary(self, profile: Dict[str, Any]) -> str:
        name = profile.get('name', 'Student')
        skills = profile.get('skills', [])
        return f"Motivated {profile.get('education_level', 'undergraduate')} student {name} with strong skills in {', '.join(skills[:3])} seeking internship opportunities to apply technical knowledge and gain practical experience."
    
    async def generate_resume_bullets(self, experience: Dict[str, Any]) -> List[str]:
        return [
            "• Developed and implemented solutions using relevant technologies",
            "• Collaborated with team members to achieve project objectives", 
            "• Applied problem-solving skills to overcome technical challenges",
            "• Gained valuable experience in professional work environment"
        ]
    
    async def tailor_resume_to_job(self, resume_content: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        tailored_content = resume_content.copy()
        tailored_content['summary'] = "Tailored summary based on job requirements (mock version)"
        return tailored_content

def get_ai_provider() -> AIProvider:
    """Factory function to get AI provider based on configuration"""
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAIProvider(settings.openai_api_key)
    else:
        return MockAIProvider()

# Convenience functions
async def generate_resume_summary(profile: Dict[str, Any]) -> str:
    """Generate resume summary using configured AI provider"""
    provider = get_ai_provider()
    return await provider.generate_resume_summary(profile)

async def generate_resume_bullets(experience: Dict[str, Any]) -> List[str]:
    """Generate resume bullets using configured AI provider"""
    provider = get_ai_provider()
    return await provider.generate_resume_bullets(experience)

async def tailor_resume_to_job(resume_content: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """Tailor resume to job using configured AI provider"""
    provider = get_ai_provider()
    return await provider.tailor_resume_to_job(resume_content, job_description)
