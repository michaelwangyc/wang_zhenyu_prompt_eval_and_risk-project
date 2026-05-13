export const METADATA = {
  TITLE: "MaterniFlow — AI-Powered OB/GYN Operation Assistant",
  DESCRIPTION: "An AI assistant for OB/GYN nurses. Query ward status, predict length-of-stay, coordinate rooms, receive alerts, and place orders through natural conversation.",
  AI_ASSISTANT_NAME: "MaterniFlow",
  KEYWORDS: [
    "AI",
    "AI Agent",
    "OB/GYN",
    "Hospital",
    "Maternity",
    "Ward Management",
    "Healthcare AI",
    "Scheduling Assistant",
  ],
} as const;

export const CDN_ASSETS = {
  HERO_IMAGE_LOW_MARGIN: "...",
  PROFILE_PHOTO: "/images/profile.png",
} as const;

export const ROUTES = {
  HOME: "/",
  CHAT: "/chat",
} as const;

export const EXTERNAL_LINKS = {
  GITHUB_REPO: "https://github.com/michaelwangyc/hospital_maternity_operation_agent-project",
  SOURCE_DB_SCHEMA_EXTRACTOR:
    "https://github.com/michaelwangyc/hospital_maternity_operation_agent-project/blob/main/labor_ward_ai/db_schema/extractor.py",
  SOURCE_AGENT_SYSTEM_PROMPT:
    "https://github.com/michaelwangyc/hospital_maternity_operation_agent-project/blob/main/labor_ward_ai/prompts/bi-agent-system-prompt.md",
  SOURCE_AGENT_DEFINITION:
    "https://github.com/michaelwangyc/hospital_maternity_operation_agent-project/blob/main/labor_ward_ai/one/one_04_agent.py",
  SOURCE_UI_BACKEND:
    "https://github.com/michaelwangyc/hospital_maternity_operation_agent-project/blob/main/api/index.py",
} as const;
