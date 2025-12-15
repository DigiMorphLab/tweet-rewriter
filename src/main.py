import argparse
import os
import sys

# Add parent directory to path to allow importing src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import TweetRewriter

def main():
    parser = argparse.ArgumentParser(description="AI Tweet Rewriter Workflow")
    parser.add_argument("--text", type=str, required=True, help="The original tweet text")
    parser.add_argument("--intent", type=str, required=True, help="The rewrite intent (e.g., 'FUD', 'Hype', 'Review')")
    parser.add_argument("--count", type=int, default=1, help="Number of variations to generate")
    parser.add_argument("--api_key", type=str, help="OpenAI API Key (optional if set in env)")
    
    args = parser.parse_args()

    rewriter = TweetRewriter(api_key=args.api_key)
    
    print(f"Original Text: {args.text}")
    print(f"Intent: {args.intent}")
    print("="*50)
    
    rewriter.run_workflow(args.text, args.intent, args.count)

if __name__ == "__main__":
    main()
