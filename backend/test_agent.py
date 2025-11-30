"""
Test script to validate the agent's tool usage
"""
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from agent_service import MappingAgent

def test_question(agent: MappingAgent, question: str):
    """Test a question and print results"""
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print('='*80)
    
    try:
        result = agent.ask(question)
        
        print(f"\n✓ ANSWER: {result['answer']}")
        print(f"\n🔧 TOOLS USED ({len(result['tool_uses'])}):")
        for tool_use in result['tool_uses']:
            print(f"  - {tool_use['tool']}({json.dumps(tool_use['input'])})")
            if 'error' in tool_use['result']:
                print(f"    ❌ ERROR: {tool_use['result']['error']}")
            else:
                print(f"    ✓ Result: {tool_use['result'].get('message', 'OK')}")
        
        print(f"\n🗺️  MAP COMMANDS ({len(result['map_commands'])}):")
        for cmd in result['map_commands']:
            print(f"  - {cmd['command']}")
            if cmd['command'] == 'highlight_features':
                print(f"    Feature IDs: {cmd['feature_ids'][:5]}... ({len(cmd['feature_ids'])} total)")
                print(f"    Color: {cmd['color']}")
            elif cmd['command'] == 'show_statistics':
                print(f"    Stats: {cmd['stats']}")
        
        if not result['map_commands']:
            print("  ⚠️  NO MAP COMMANDS GENERATED!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result


def main():
    """Run test suite"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not found in .env")
        return
    
    print("🧪 TESTING AGENT TOOL USAGE")
    
    # Test cases
    test_cases = [
        "show me all stop signs",
        "show me all guardrails",
        "which image has the most features?",
        "show me images containing stop signs",
        "which image has the most damaged features?",
    ]
    
    for question in test_cases:
        # Create fresh agent for each question to avoid context pollution
        agent = MappingAgent(api_key)
        print(f"\nCampaign: {agent.campaign.total_features} features, {agent.campaign.total_images} images")
        test_question(agent, question)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

