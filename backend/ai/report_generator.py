from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from backend.config import Config

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate AI-powered incident reports."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = self._get_client()
    
    def _get_client(self):
        """Get appropriate AI client based on configuration."""
        if self.config.USE_OPENAI and self.config.OPENAI_API_KEY:
            from .openai_client import OpenAIClient
            return OpenAIClient(self.config.OPENAI_API_KEY, self.config.OPENAI_MODEL)
        else:
            from .ollama_client import OllamaClient
            return OllamaClient(self.config.OLLAMA_BASE_URL, self.config.OLLAMA_MODEL)
    
    def generate_report(self, incident_data: Dict, events: List[Dict]) -> Dict:
        """Generate complete incident report."""
        start_time = datetime.now()
        
        try:
            # Prepare context
            context = self._prepare_context(incident_data, events)
            
            # Generate report sections
            report = {
                'executive_summary': self._generate_executive_summary(context),
                'incident_overview': self._generate_incident_overview(context),
                'timeline': self._generate_timeline(context),
                'root_cause_analysis': self._generate_root_cause_analysis(context),
                'impact_assessment': self._generate_impact_assessment(context),
                'systems_affected': self._generate_systems_affected(context),
                'resolution_steps': self._generate_resolution_steps(context),
                'recommendations': self._generate_recommendations(context),
                'preventive_actions': self._generate_preventive_actions(context),
                'lessons_learned': self._generate_lessons_learned(context),
                'ai_model_used': self._get_model_name(),
                'confidence_score': self._calculate_confidence_score(context)
            }
            
            generation_time = (datetime.now() - start_time).total_seconds()
            report['generation_time'] = generation_time
            
            logger.info(f"Report generated in {generation_time:.2f} seconds")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    def _prepare_context(self, incident_data: Dict, events: List[Dict]) -> str:
        """Prepare context for AI generation."""
        context = f"""
Incident Details:
- Title: {incident_data.get('title', 'Unknown')}
- Description: {incident_data.get('description', 'No description')}
- Severity: {incident_data.get('severity', 'Unknown')}
- Type: {incident_data.get('incident_type', 'Unknown')}
- Detected: {incident_data.get('detected_at', 'Unknown')}

Event Summary:
- Total Events: {len(events)}
- Error Events: {len([e for e in events if e.get('level') in ['error', 'critical']])}
- Warning Events: {len([e for e in events if e.get('level') == 'warning'])}

Sample Events:
"""
        # Add sample events (limit to avoid token limits)
        for event in events[:20]:
            context += f"\n- [{event.get('timestamp', 'Unknown')}] {event.get('level', 'info').upper()}: {event.get('message', 'No message')}"
        
        return context
    
    def _generate_executive_summary(self, context: str) -> str:
        """Generate executive summary."""
        prompt = f"""Based on the following incident context, write a concise executive summary (2-3 paragraphs):
{context}

The summary should include:
1. What happened
2. Immediate impact
3. Current status
"""
        return self.client.generate(prompt)
    
    def _generate_incident_overview(self, context: str) -> str:
        """Generate incident overview."""
        prompt = f"""Based on the incident context, provide a detailed incident overview:
{context}

Include:
1. Detailed description of the incident
2. Technical details
3. Affected components
"""
        return self.client.generate(prompt)
    
    def _generate_timeline(self, context: str) -> str:
        """Generate incident timeline."""
        prompt = f"""Based on the incident context, create a chronological timeline of events:
{context}

Format as a bulleted list with timestamps and key milestones.
"""
        return self.client.generate(prompt)
    
    def _generate_root_cause_analysis(self, context: str) -> str:
        """Generate root cause analysis."""
        prompt = f"""Based on the incident context, perform a root cause analysis:
{context}

Include:
1. Primary root cause
2. Contributing factors
3. Evidence supporting the analysis
"""
        return self.client.generate(prompt)
    
    def _generate_impact_assessment(self, context: str) -> str:
        """Generate impact assessment."""
        prompt = f"""Based on the incident context, assess the impact:
{context}

Include:
1. Business impact
2. Technical impact
3. User impact
4. Data impact (if any)
"""
        return self.client.generate(prompt)
    
    def _generate_systems_affected(self, context: str) -> str:
        """Generate systems affected section."""
        prompt = f"""Based on the incident context, list all systems and components affected:
{context}

Format as a structured list with system names and impact levels.
"""
        return self.client.generate(prompt)
    
    def _generate_resolution_steps(self, context: str) -> str:
        """Generate resolution steps."""
        prompt = f"""Based on the incident context, provide detailed resolution steps:
{context}

Include:
1. Immediate actions taken
2. Additional steps needed
3. Verification steps
"""
        return self.client.generate(prompt)
    
    def _generate_recommendations(self, context: str) -> str:
        """Generate recommendations."""
        prompt = f"""Based on the incident context, provide recommendations for improvement:
{context}

Include both short-term and long-term recommendations.
"""
        return self.client.generate(prompt)
    
    def _generate_preventive_actions(self, context: str) -> str:
        """Generate preventive actions."""
        prompt = f"""Based on the incident context, suggest preventive actions:
{context}

Focus on:
1. Process improvements
2. Technical safeguards
3. Monitoring enhancements
"""
        return self.client.generate(prompt)
    
    def _generate_lessons_learned(self, context: str) -> str:
        """Generate lessons learned."""
        prompt = f"""Based on the incident context, document lessons learned:
{context}

Include:
1. What went well
2. What could be improved
3. Key takeaways
"""
        return self.client.generate(prompt)
    
    def _get_model_name(self) -> str:
        """Get the name of the AI model being used."""
        if self.config.USE_OPENAI:
            return f"OpenAI {self.config.OPENAI_MODEL}"
        else:
            return f"Ollama {self.config.OLLAMA_MODEL}"
    
    def _calculate_confidence_score(self, context: str) -> float:
        """Calculate confidence score for the report."""
        # Simple heuristic based on event count and data quality
        event_count = context.count('Event Summary:')
        if event_count > 0:
            # More events generally means higher confidence
            score = min(0.7 + (event_count * 0.01), 0.95)
        else:
            score = 0.5
        return round(score, 2)
