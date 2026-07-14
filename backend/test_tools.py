import os
import sys

# Ensure backend dir is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

import agent
from schemas import InteractionBase

message = "Met with Dr. Sarah Jenkins. Left 10 samples of OncoBoost."
form_state = InteractionBase().model_dump()

result = agent.run_agent(message, form_state)
print("UPDATED STATE:")
print(result["updated_form_state"])
print("\nSUGGESTED FOLLOW UPS:")
print(result["suggested_follow_ups"])
print("\nREPLY MESSAGE:")
print(result["reply_message"])
