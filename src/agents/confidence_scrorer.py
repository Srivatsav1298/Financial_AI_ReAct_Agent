"""
Confidence Scoring System
Evaluates agent confidence in answers based on multiple criteria
"""

from typing import Dict, Any, List
import re


class ConfidenceScorer:
    """
    Evaluates confidence in agent responses
    Scores based on:
    - Data source quality (SSB = high confidence)
    - Reasoning completeness (ReAct iterations)
    - Tool usage consistency
    - Answer specificity
    """
    
    def __init__(self):
        self.confidence_levels = {
            'very_high': (0.9, 1.0),
            'high': (0.75, 0.9),
            'medium': (0.5, 0.75),
            'low': (0.25, 0.5),
            'very_low': (0.0, 0.25)
        }
    
    def score_baseline_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Score baseline agent answer confidence"""
        
        score = 0.5  # Start at medium
        factors = []
        
        # Check if tool was used
        if result.get('tool_used', False):
            score += 0.2
            factors.append("Used SSB data source (+0.2)")
        else:
            score -= 0.2
            factors.append("No data source verification (-0.2)")
        
        # Check answer length (too short = less confident)
        answer_length = len(result.get('answer', ''))
        if answer_length > 100:
            score += 0.1
            factors.append("Detailed answer (+0.1)")
        elif answer_length < 50:
            score -= 0.1
            factors.append("Brief answer (-0.1)")
        
        # Check for numerical values (specific = confident)
        if re.search(r'\d{1,3}[,\d]*\s*NOK', result.get('answer', '')):
            score += 0.15
            factors.append("Specific numerical values (+0.15)")
        
        # Check for SSB citation
        if 'SSB' in result.get('answer', '') or 'Statistics Norway' in result.get('answer', ''):
            score += 0.1
            factors.append("Explicit source citation (+0.1)")
        
        # Normalize to 0-1 range
        score = max(0.0, min(1.0, score))
        
        return {
            'confidence_score': round(score, 3),
            'confidence_level': self._get_confidence_level(score),
            'factors': factors,
            'explanation': self._generate_explanation(score, factors)
        }
    
    def score_react_answer(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Score ReAct agent answer confidence"""
        
        score = 0.6  # Start higher for ReAct (explicit reasoning)
        factors = []
        
        # ReAct always uses tools
        score += 0.15
        factors.append("Systematic tool usage (+0.15)")
        
        # Check iterations (more iterations = more thorough)
        iterations = result.get('iterations', 1)
        if iterations >= 2:
            score += min(0.15, iterations * 0.05)
            factors.append(f"{iterations} reasoning iterations (+{min(0.15, iterations * 0.05):.2f})")
        
        # Check reasoning steps
        reasoning_steps = result.get('reasoning_steps', [])
        if len(reasoning_steps) > 0:
            score += 0.1
            factors.append("Explicit reasoning trace (+0.1)")
        
        # Check answer completeness
        answer = result.get('answer', '')
        if len(answer) > 150:
            score += 0.05
            factors.append("Comprehensive answer (+0.05)")
        
        # Check for multiple data points
        num_values = len(re.findall(r'\d{1,3}[,\d]*\s*NOK', answer))
        if num_values >= 2:
            score += 0.1
            factors.append(f"Multiple data points ({num_values}) (+0.1)")
        
        # Normalize
        score = max(0.0, min(1.0, score))
        
        return {
            'confidence_score': round(score, 3),
            'confidence_level': self._get_confidence_level(score),
            'factors': factors,
            'explanation': self._generate_explanation(score, factors)
        }
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        for level, (low, high) in self.confidence_levels.items():
            if low <= score < high:
                return level
        return 'very_high' if score >= 0.9 else 'very_low'
    
    def _generate_explanation(self, score: float, factors: List[str]) -> str:
        """Generate human-readable confidence explanation"""
        level = self._get_confidence_level(score)
        
        explanation = f"Confidence: {level.replace('_', ' ').title()} ({score:.2%})\n\n"
        explanation += "Contributing factors:\n"
        for factor in factors:
            explanation += f"  • {factor}\n"
        
        return explanation
    
    def compare_confidence(self, baseline_conf: Dict, react_conf: Dict) -> Dict[str, Any]:
        """Compare confidence between baseline and ReAct"""
        
        baseline_score = baseline_conf['confidence_score']
        react_score = react_conf['confidence_score']
        
        difference = react_score - baseline_score
        
        analysis = {
            'baseline_score': baseline_score,
            'react_score': react_score,
            'difference': round(difference, 3),
            'react_more_confident': react_score > baseline_score,
            'percentage_improvement': round((difference / baseline_score * 100) if baseline_score > 0 else 0, 1)
        }
        
        if difference > 0.2:
            analysis['interpretation'] = "ReAct shows significantly higher confidence"
        elif difference > 0.05:
            analysis['interpretation'] = "ReAct shows moderately higher confidence"
        elif abs(difference) <= 0.05:
            analysis['interpretation'] = "Similar confidence levels"
        else:
            analysis['interpretation'] = "Baseline shows higher confidence"
        
        return analysis


def test_confidence_scorer():
    """Test the confidence scoring system"""
    print("🧪 Testing Confidence Scorer\n")
    
    scorer = ConfidenceScorer()
    
    # Test baseline result
    baseline_result = {
        'question': 'How much on housing?',
        'answer': 'Norwegian households spend 11,332 NOK per month on housing according to SSB data.',
        'tool_used': True,
        'elapsed_time': 5.2
    }
    
    baseline_conf = scorer.score_baseline_answer(baseline_result)
    print("📊 Baseline Confidence:")
    print(f"   Score: {baseline_conf['confidence_score']}")
    print(f"   Level: {baseline_conf['confidence_level']}")
    print(f"\n{baseline_conf['explanation']}")
    
    # Test ReAct result
    react_result = {
        'question': 'How much on housing?',
        'answer': 'Based on Statistics Norway data, Norwegian households spend an average of 11,332 NOK per month on housing (135,982 NOK annually).',
        'iterations': 2,
        'reasoning_steps': [
            {'iteration': 1, 'action': 'get_spending', 'observation': '11,332 NOK'},
            {'iteration': 2, 'action': 'format_answer'}
        ],
        'elapsed_time': 9.8
    }
    
    react_conf = scorer.score_react_answer(react_result)
    print("\n" + "="*60)
    print("📊 ReAct Confidence:")
    print(f"   Score: {react_conf['confidence_score']}")
    print(f"   Level: {react_conf['confidence_level']}")
    print(f"\n{react_conf['explanation']}")
    
    # Compare
    comparison = scorer.compare_confidence(baseline_conf, react_conf)
    print("\n" + "="*60)
    print("📊 Comparison:")
    print(f"   Baseline: {comparison['baseline_score']:.3f}")
    print(f"   ReAct: {comparison['react_score']:.3f}")
    print(f"   Difference: {comparison['difference']:.3f} ({comparison['percentage_improvement']:.1f}%)")
    print(f"   {comparison['interpretation']}")
    
    print("\nConfidence Scorer tests complete!")


if __name__ == "__main__":
    test_confidence_scorer()