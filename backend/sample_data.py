"""
Sample data for Meeting Studio.
Contains realistic pre-processed meetings and initial LLM calls.
"""

from typing import List, Dict, Any

SPEAKER_COLORS = ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#db2777', '#ca8a04']

def get_initial_meetings() -> List[Dict[str, Any]]:
    # Meeting 1: Sprint Review
    m1_speakers = [
        {"id": "s1", "label": "Speaker 1", "displayName": "Priya Sharma", "role": "Product Manager", "color": SPEAKER_COLORS[0]},
        {"id": "s2", "label": "Speaker 2", "displayName": "Raj Patel", "role": "Engineering Lead", "color": SPEAKER_COLORS[1]},
        {"id": "s3", "label": "Speaker 3", "displayName": "Sarah Chen", "role": "Designer", "color": SPEAKER_COLORS[2]},
        {"id": "s4", "label": "Speaker 4", "displayName": "Mike Johnson", "role": "QA Lead", "color": SPEAKER_COLORS[3]},
    ]

    m1_segments = [
        {"id": "g1", "meetingId": "demo-1", "idx": 0, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 0, "endSec": 12, "text": "Good morning everyone, thanks for joining. Let's get started with the sprint review. Raj, can you walk us through the engineering updates?", "sentiment": "positive"},
        {"id": "g2", "meetingId": "demo-1", "idx": 1, "speakerId": "s2", "speakerLabel": "Raj Patel", "startSec": 12, "endSec": 38, "text": "Sure. So this sprint we completed the authentication refactor and the new API endpoints for the dashboard. The team ran into some issues with the caching layer but we resolved it by switching to Redis. Velocity was 42 points, up from 38 last sprint.", "sentiment": "neutral"},
        {"id": "g3", "meetingId": "demo-1", "idx": 2, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 38, "endSec": 52, "text": "That's great progress. Sarah, how did the design work go this sprint?", "sentiment": "positive"},
        {"id": "g4", "meetingId": "demo-1", "idx": 3, "speakerId": "s3", "speakerLabel": "Sarah Chen", "startSec": 52, "endSec": 85, "text": "I finished the new dashboard mockups. I've gone through three iterations based on feedback from the user research sessions. The key change is simplifying the navigation — we moved from a sidebar to a top-level tab structure. I think it's much cleaner now.", "sentiment": "neutral"},
        {"id": "g5", "meetingId": "demo-1", "idx": 4, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 85, "endSec": 98, "text": "Love the direction. Let's make sure we get feedback from the client on Thursday. Mike, what's the QA situation?", "sentiment": "positive"},
        {"id": "g6", "meetingId": "demo-1", "idx": 5, "speakerId": "s4", "speakerLabel": "Mike Johnson", "startSec": 98, "endSec": 130, "text": "We've completed regression testing for the auth refactor — no critical bugs found. However, I found three medium-priority issues in the new API endpoints. Two are related to error handling and one is a race condition in the concurrent request handling. I've logged all three in Jira.", "sentiment": "negative"},
        {"id": "g7", "meetingId": "demo-1", "idx": 6, "speakerId": "s2", "speakerLabel": "Raj Patel", "startSec": 130, "endSec": 155, "text": "I'll take a look at the race condition issue this week. The error handling ones we can address in the next sprint. Actually, I think we should prioritize the race condition because it could affect production stability.", "sentiment": "neutral"},
        {"id": "g8", "meetingId": "demo-1", "idx": 7, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 155, "endSec": 178, "text": "Agreed. Let's make the race condition fix a priority for next sprint. Now, regarding the roadmap — I want to discuss the Q3 priorities. We need to decide between focusing on the mobile app or the analytics platform.", "sentiment": "neutral"},
        {"id": "g9", "meetingId": "demo-1", "idx": 8, "speakerId": "s2", "speakerLabel": "Raj Patel", "startSec": 178, "endSec": 205, "text": "I strongly recommend we prioritize the analytics platform. The client has been asking for it since Q1, and we already have the infrastructure from the dashboard work. The mobile app can wait until Q4.", "sentiment": "neutral"},
        {"id": "g10", "meetingId": "demo-1", "idx": 9, "speakerId": "s3", "speakerLabel": "Sarah Chen", "startSec": 205, "endSec": 228, "text": "I agree with Raj. The analytics platform builds on what we've already done. Plus, the design system is ready for it. For the mobile app, we'd need to start from scratch with mobile-specific designs.", "sentiment": "positive"},
        {"id": "g11", "meetingId": "demo-1", "idx": 10, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 228, "endSec": 250, "text": "Okay, let's go with the analytics platform for Q3 then. That's decided. Raj, can you put together a technical plan by next Friday? We'll review it in the next planning meeting.", "sentiment": "positive"},
        {"id": "g12", "meetingId": "demo-1", "idx": 11, "speakerId": "s2", "speakerLabel": "Raj Patel", "startSec": 250, "endSec": 268, "text": "Yes, I'll have the technical plan ready by next Friday. I'll include resource estimates, timeline, and key risks. I'll also need Sarah's input on the UI components we'll need.", "sentiment": "neutral"},
        {"id": "g13", "meetingId": "demo-1", "idx": 12, "speakerId": "s3", "speakerLabel": "Sarah Chen", "startSec": 268, "endSec": 282, "text": "I can start working on the component library next week. I'll have the base components ready by the 20th so Raj can use them in the technical plan.", "sentiment": "positive"},
        {"id": "g14", "meetingId": "demo-1", "idx": 13, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 282, "endSec": 305, "text": "Perfect. Mike, I need you to set up the test environment for the analytics platform by the end of the month. We need it ready before development starts in Q3.", "sentiment": "positive"},
        {"id": "g15", "meetingId": "demo-1", "idx": 14, "speakerId": "s4", "speakerLabel": "Mike Johnson", "startSec": 305, "endSec": 325, "text": "I'll get the test environment configured. I'll need the infrastructure requirements from Raj by Wednesday to make sure I provision the right resources.", "sentiment": "neutral"},
        {"id": "g16", "meetingId": "demo-1", "idx": 15, "speakerId": "s2", "speakerLabel": "Raj Patel", "startSec": 325, "endSec": 340, "text": "I'll send you the requirements by Wednesday. No problem.", "sentiment": "positive"},
        {"id": "g17", "meetingId": "demo-1", "idx": 16, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 340, "endSec": 365, "text": "Great. One more thing — the client demo is scheduled for July 15th. Sarah, can you prepare a demo of the new dashboard design? And Raj, let's show the API performance improvements.", "sentiment": "positive"},
        {"id": "g18", "meetingId": "demo-1", "idx": 17, "speakerId": "s3", "speakerLabel": "Sarah Chen", "startSec": 365, "endSec": 378, "text": "I'll prepare the dashboard demo. I'll have a clickable prototype ready by July 12th.", "sentiment": "positive"},
        {"id": "g19", "meetingId": "demo-1", "idx": 18, "speakerId": "s2", "speakerLabel": "Raj Patel", "startSec": 378, "endSec": 395, "text": "I'll put together a performance comparison showing the before and after metrics. I'll have it ready by July 13th.", "sentiment": "positive"},
        {"id": "g20", "meetingId": "demo-1", "idx": 19, "speakerId": "s1", "speakerLabel": "Priya Sharma", "startSec": 395, "endSec": 420, "text": "Excellent. Let's also make sure we send out the meeting notes to all stakeholders. I'll handle that by end of day tomorrow. Thanks everyone, great sprint review.", "sentiment": "positive"},
    ]

    m1_decisions = [
        {"id": "d1", "meetingId": "demo-1", "text": "Prioritize the analytics platform over the mobile app for Q3.", "decidedBy": "Priya Sharma", "rationale": "Client demand since Q1, existing infrastructure, and design system readiness make it the higher-impact choice.", "quote": "let's go with the analytics platform for Q3 then. That's decided.", "startSec": 228, "verified": True, "confidence": 0.96},
        {"id": "d2", "meetingId": "demo-1", "text": "Race condition fix is a priority for next sprint.", "decidedBy": "Priya Sharma", "rationale": "Production stability risk requires immediate attention before the next release.", "quote": "Let's make the race condition fix a priority for next sprint.", "startSec": 155, "verified": True, "confidence": 0.93},
        {"id": "d3", "meetingId": "demo-1", "text": "Client demo scheduled for July 15th covering dashboard design & API metrics.", "decidedBy": "Priya Sharma", "rationale": "Client needs visibility into progress before Q3 kick-off.", "quote": "the client demo is scheduled for July 15th", "startSec": 340, "verified": True, "confidence": 0.91},
    ]

    m1_tasks = [
        {"id": "t1", "meetingId": "demo-1", "title": "Create technical plan for analytics platform", "owner": "Raj Patel", "deadline": "2026-10-10", "deadlineRaw": "by next Friday", "deadlineAmbiguous": False, "priority": "high", "status": "todo", "quote": "can you put together a technical plan by next Friday?", "startSec": 228, "verified": True, "confidence": 0.94},
        {"id": "t2", "meetingId": "demo-1", "title": "Build base component library for analytics UI", "owner": "Sarah Chen", "deadline": "2026-10-20", "deadlineRaw": "by the 20th", "deadlineAmbiguous": False, "priority": "medium", "status": "todo", "quote": "I'll have the base components ready by the 20th", "startSec": 268, "verified": True, "confidence": 0.90},
        {"id": "t3", "meetingId": "demo-1", "title": "Set up test environment for analytics platform", "owner": "Mike Johnson", "deadline": "2026-10-31", "deadlineRaw": "by the end of the month", "deadlineAmbiguous": False, "priority": "high", "status": "todo", "quote": "I need you to set up the test environment for the analytics platform by the end of the month", "startSec": 282, "verified": True, "confidence": 0.92},
        {"id": "t4", "meetingId": "demo-1", "title": "Send infrastructure requirements to Mike", "owner": "Raj Patel", "deadline": "2026-10-07", "deadlineRaw": "by Wednesday", "deadlineAmbiguous": False, "priority": "high", "status": "doing", "quote": "I'll send you the requirements by Wednesday", "startSec": 325, "verified": True, "confidence": 0.93},
        {"id": "t5", "meetingId": "demo-1", "title": "Prepare clickable dashboard prototype for client demo", "owner": "Sarah Chen", "deadline": "2026-10-12", "deadlineRaw": "by July 12th", "deadlineAmbiguous": False, "priority": "high", "status": "todo", "quote": "I'll have a clickable prototype ready by July 12th.", "startSec": 365, "verified": True, "confidence": 0.88},
        {"id": "t6", "meetingId": "demo-1", "title": "Fix race condition in concurrent request handling", "owner": "Raj Patel", "deadline": "2026-10-11", "deadlineRaw": "next sprint", "deadlineAmbiguous": True, "priority": "high", "status": "todo", "quote": "I'll take a look at the race condition issue this week", "startSec": 130, "verified": True, "confidence": 0.85},
        {"id": "t7", "meetingId": "demo-1", "title": "Send meeting notes to all stakeholders", "owner": "Priya Sharma", "deadline": "2026-10-05", "deadlineRaw": "by end of day tomorrow", "deadlineAmbiguous": False, "priority": "medium", "status": "done", "quote": "I'll handle that by end of day tomorrow", "startSec": 395, "verified": True, "confidence": 0.90},
    ]

    m1_insights = [
        {"id": "i1", "meetingId": "demo-1", "kind": "opportunity", "text": "Analytics platform leverages existing dashboard infrastructure, reducing development effort significantly.", "quote": "we already have the infrastructure from the dashboard work", "startSec": 178, "confidence": 0.92},
        {"id": "i2", "meetingId": "demo-1", "kind": "risk", "text": "Race condition in concurrent request handling could affect production stability if not addressed promptly.", "quote": "one is a race condition in the concurrent request handling", "startSec": 98, "confidence": 0.88},
        {"id": "i3", "meetingId": "demo-1", "kind": "insight", "text": "Sprint velocity improved from 38 to 42 points, indicating increasing engineering capacity.", "quote": "Velocity was 42 points, up from 38 last sprint.", "startSec": 12, "confidence": 0.95},
    ]

    m1_critic_log = [
        {"id": "cr1", "meetingId": "demo-1", "itemType": "task", "itemRef": "Fix race condition in concurrent request handling", "action": "kept", "reason": "Quote found in transcript at 02:10. Owner Raj Patel explicitly stated intent to fix."},
        {"id": "cr2", "meetingId": "demo-1", "itemType": "decision", "itemRef": "Prioritize analytics platform for Q3", "action": "kept", "reason": "Quote found at 03:48. Decision stated by Priya with clear rationale from multiple speakers."},
        {"id": "cr3", "meetingId": "demo-1", "itemType": "task", "itemRef": "Update mobile app roadmap", "action": "removed", "reason": "No quote found in transcript. No speaker explicitly committed to this task."},
    ]

    meeting1 = {
        "id": "demo-1",
        "title": "Sprint Review & Q3 Planning",
        "meetingDate": "2026-10-04",
        "sourceFilename": "sprint-review-oct4.mp3",
        "mediaType": "audio",
        "durationSec": 420,
        "language": "en",
        "meetingType": "planning",
        "status": "done",
        "statusDetail": "Processing complete",
        "progressPct": 100,
        "confidentialMode": False,
        "healthScore": 82,
        "tags": ["sprint-review", "q3-planning", "engineering"],
        "createdAt": "2026-10-04T10:00:00Z",
        "updatedAt": "2026-10-04T10:30:00Z",
        "speakers": m1_speakers,
        "segments": m1_segments,
        "summary": {
            "meetingId": "demo-1",
            "tldr": "The team reviewed sprint progress (velocity increased to 42 points), prioritized fixing a QA race condition, and unanimously decided to prioritize the analytics platform for Q3 over the mobile app. Key deliverables and deadlines were locked down for next sprint.",
            "oneMinute": "The sprint review covered engineering, design, and QA updates. Raj reported completing the auth refactor and new API endpoints, with velocity increasing to 42 points. Sarah presented three iterations of dashboard mockups with simplified tab navigation. Mike flagged three bugs in the API endpoints, including a race condition in concurrent request handling that was prioritized for immediate resolution. The team decided to focus Q3 on the analytics platform, citing existing infrastructure readiness and client demand. Key deadlines include Raj's technical plan by Oct 10, component library by Oct 20, and test environment by Oct 31.",
            "detailed": [
                {"topic": "Engineering Updates", "text": "Auth refactor completed, Redis caching implemented, sprint velocity at 42 points.", "startSec": 0},
                {"topic": "Design Mockups", "text": "Sarah completed three iterations of tab-based navigation.", "startSec": 52},
                {"topic": "QA Findings", "text": "Race condition flagged and prioritized for next sprint.", "startSec": 98},
                {"topic": "Q3 Roadmap Decision", "text": "Analytics platform selected over mobile app due to client demand and existing groundwork.", "startSec": 155},
                {"topic": "Action Items", "text": "Technical plan, component library, and test environment scheduled.", "startSec": 228}
            ],
            "topics": ["Sprint Review", "Engineering", "Design", "QA", "Q3 Roadmap", "Action Items"],
            "outputLanguage": "en"
        },
        "insights": m1_insights,
        "decisions": m1_decisions,
        "tasks": m1_tasks,
        "criticLog": m1_critic_log,
        "analytics": {
            "meetingId": "demo-1",
            "talkTime": [
                {"speakerId": "s1", "speakerLabel": "Priya Sharma", "seconds": 155, "percentage": 36.9},
                {"speakerId": "s2", "speakerLabel": "Raj Patel", "seconds": 130, "percentage": 31.0},
                {"speakerId": "s3", "speakerLabel": "Sarah Chen", "seconds": 80, "percentage": 19.0},
                {"speakerId": "s4", "speakerLabel": "Mike Johnson", "seconds": 55, "percentage": 13.1},
            ],
            "avgTurnLength": 21.0,
            "interruptions": 2,
            "questionsAsked": 4,
            "healthScore": 82
        },
        "chatMessages": [
            {"id": "cm1", "meetingId": "demo-1", "role": "user", "content": "What was decided about Q3 priorities?", "createdAt": "2026-10-04T11:00:00Z"},
            {"id": "cm2", "meetingId": "demo-1", "role": "assistant", "content": "The team decided to prioritize the analytics platform over the mobile app for Q3. Priya Sharma stated: \"let's go with the analytics platform for Q3 then. That's decided.\" The rationale was that the client has been requesting it since Q1, and the design system is already ready.", "citations": [{"speaker": "Priya Sharma", "timeSec": 228, "text": "let's go with the analytics platform for Q3 then. That's decided."}], "createdAt": "2026-10-04T11:00:05Z"}
        ]
    }

    # Meeting 2: Client Kickoff
    m2_speakers = [
        {"id": "s1b", "label": "Speaker 1", "displayName": "Priya Sharma", "role": "Product Manager", "color": SPEAKER_COLORS[0]},
        {"id": "s2b", "label": "Speaker 2", "displayName": "Alex Rivera", "role": "Client Contact (Acme Corp)", "color": SPEAKER_COLORS[1]},
        {"id": "s3b", "label": "Speaker 3", "displayName": "David Kim", "role": "Sales Engineer", "color": SPEAKER_COLORS[2]},
    ]
    m2_segments = [
        {"id": "h1", "meetingId": "demo-2", "idx": 0, "speakerId": "s1b", "speakerLabel": "Priya Sharma", "startSec": 0, "endSec": 20, "text": "Welcome Alex, thanks for taking the time today. We're excited to kick off this project with Acme Corp. David from our sales engineering team is also here.", "sentiment": "positive"},
        {"id": "h2", "meetingId": "demo-2", "idx": 1, "speakerId": "s2b", "speakerLabel": "Alex Rivera", "startSec": 20, "endSec": 55, "text": "Thanks Priya. The main goal is to get a custom analytics dashboard built that integrates with our Salesforce CRM. We need it to show real-time sales metrics, customer segmentation, and revenue forecasting.", "sentiment": "neutral"},
        {"id": "h3", "meetingId": "demo-2", "idx": 2, "speakerId": "s3b", "speakerLabel": "David Kim", "startSec": 55, "endSec": 85, "text": "The analytics platform we've been building handles real-time CRM data integration. We'll start with data mapping and sandbox environment setup.", "sentiment": "positive"},
        {"id": "h4", "meetingId": "demo-2", "idx": 3, "speakerId": "s1b", "speakerLabel": "Priya Sharma", "startSec": 85, "endSec": 120, "text": "We propose a 12-week build with a working prototype by week 6 and the forecasting module ready before your December board meeting.", "sentiment": "positive"},
    ]
    meeting2 = {
        "id": "demo-2",
        "title": "Client Kickoff Call — Acme Corp",
        "meetingDate": "2026-09-26",
        "sourceFilename": "acme-kickoff-sep26.mp4",
        "mediaType": "video",
        "durationSec": 365,
        "language": "en",
        "meetingType": "client_call",
        "status": "done",
        "statusDetail": "Processing complete",
        "progressPct": 100,
        "confidentialMode": True,
        "healthScore": 86,
        "tags": ["client", "kickoff", "acme"],
        "createdAt": "2026-09-26T14:00:00Z",
        "updatedAt": "2026-09-26T14:45:00Z",
        "speakers": m2_speakers,
        "segments": m2_segments,
        "summary": {
            "meetingId": "demo-2",
            "tldr": "Acme Corp project kickoff for custom Salesforce-integrated analytics dashboard. Phased 12-week timeline agreed with a tangible prototype scheduled for week 6.",
            "oneMinute": "The kickoff meeting established scope for Acme Corp's custom analytics dashboard integrating with Salesforce CRM. The project follows a 12-week build plan: Phase 1 core metrics, Phase 2 forecasting before December board meeting, and Phase 3 segmentation. David Kim will test API connectivity and establish the sandbox environment.",
            "detailed": [
                {"topic": "CRM Integration Scope", "text": "Salesforce real-time integration required for sales velocity and forecasting.", "startSec": 0},
                {"topic": "Timeline & Milestones", "text": "Week 6 prototype demo committed, with forecasting delivered before Dec board meeting.", "startSec": 85}
            ],
            "topics": ["Scope", "Salesforce", "Timeline", "Forecasting"],
            "outputLanguage": "en"
        },
        "insights": [
            {"id": "i2-1", "meetingId": "demo-2", "kind": "risk", "text": "Forecasting module must be delivered prior to December board meeting.", "quote": "we need forecasting module before board meeting", "startSec": 85, "confidence": 0.92}
        ],
        "decisions": [
            {"id": "d2-1", "meetingId": "demo-2", "text": "12-week phased build with Week 6 prototype demo.", "decidedBy": "Priya Sharma", "rationale": "Client alignment on milestone deliverables.", "quote": "We propose a 12-week build", "startSec": 85, "verified": True, "confidence": 0.95}
        ],
        "tasks": [
            {"id": "t2-1", "meetingId": "demo-2", "title": "Test Salesforce API connection and configure sandbox", "owner": "David Kim", "deadline": "2026-10-08", "deadlineRaw": "this week", "deadlineAmbiguous": False, "priority": "high", "status": "doing", "quote": "start with data mapping and sandbox", "startSec": 55, "verified": True, "confidence": 0.93}
        ],
        "criticLog": [],
        "analytics": {
            "meetingId": "demo-2",
            "talkTime": [
                {"speakerId": "s1b", "speakerLabel": "Priya Sharma", "seconds": 140, "percentage": 38.4},
                {"speakerId": "s2b", "speakerLabel": "Alex Rivera", "seconds": 150, "percentage": 41.1},
                {"speakerId": "s3b", "speakerLabel": "David Kim", "seconds": 75, "percentage": 20.5}
            ],
            "avgTurnLength": 22.0,
            "interruptions": 1,
            "questionsAsked": 3,
            "healthScore": 86
        },
        "chatMessages": []
    }

    # Meeting 3: Senior Engineer Interview
    m3_speakers = [
        {"id": "s1c", "label": "Speaker 1", "displayName": "Raj Patel", "role": "Engineering Lead", "color": SPEAKER_COLORS[1]},
        {"id": "s2c", "label": "Speaker 2", "displayName": "Emily Brown", "role": "Candidate", "color": SPEAKER_COLORS[4]},
    ]
    m3_segments = [
        {"id": "j1", "meetingId": "demo-3", "idx": 0, "speakerId": "s1c", "speakerLabel": "Raj Patel", "startSec": 0, "endSec": 18, "text": "Hi Emily, thanks for coming in today. I'm Raj, the engineering lead. Let's start with your background.", "sentiment": "positive"},
        {"id": "j2", "meetingId": "demo-3", "idx": 1, "speakerId": "s2c", "speakerLabel": "Emily Brown", "startSec": 18, "endSec": 55, "text": "I've been working as a senior engineer for 4 years with React, TypeScript, and Python backends. I built real-time streaming dashboards and RAG pipelines.", "sentiment": "positive"},
        {"id": "j3", "meetingId": "demo-3", "idx": 2, "speakerId": "s1c", "speakerLabel": "Raj Patel", "startSec": 55, "endSec": 80, "text": "Great. What is your notice period and availability?", "sentiment": "neutral"},
        {"id": "j4", "meetingId": "demo-3", "idx": 3, "speakerId": "s2c", "speakerLabel": "Emily Brown", "startSec": 80, "endSec": 105, "text": "I have a two-week notice period and could join immediately following.", "sentiment": "positive"},
    ]
    meeting3 = {
        "id": "demo-3",
        "title": "Senior Engineer Interview — Emily Brown",
        "meetingDate": "2026-09-30",
        "sourceFilename": "interview-emily-sep30.txt",
        "mediaType": "transcript",
        "durationSec": 490,
        "language": "en",
        "meetingType": "interview",
        "status": "done",
        "statusDetail": "Processing complete",
        "progressPct": 100,
        "confidentialMode": True,
        "healthScore": 92,
        "tags": ["interview", "hiring", "engineering"],
        "createdAt": "2026-09-30T11:00:00Z",
        "updatedAt": "2026-09-30T11:20:00Z",
        "speakers": m3_speakers,
        "segments": m3_segments,
        "summary": {
            "meetingId": "demo-3",
            "tldr": "Technical interview with senior engineer candidate Emily Brown covering state management, system design, and Python backend services. Strong fit with two-week notice period.",
            "oneMinute": "Raj interviewed Emily Brown for the Senior Engineer role. Emily demonstrated deep knowledge of distributed streaming systems, RAG architectures, and test automation. Availability confirmed at 2-week notice period.",
            "detailed": [
                {"topic": "Candidate Experience", "text": "4 years full-stack experience with real-time systems.", "startSec": 18},
                {"topic": "Availability", "text": "Ready to start within two weeks.", "startSec": 80}
            ],
            "topics": ["Technical Interview", "System Design", "Availability"],
            "outputLanguage": "en"
        },
        "insights": [
            {"id": "i3-1", "meetingId": "demo-3", "kind": "opportunity", "text": "Emily brings proven experience in streaming analytics matching our Q3 tech stack.", "quote": "built real-time streaming dashboards and RAG pipelines", "startSec": 18, "confidence": 0.94}
        ],
        "decisions": [
            {"id": "d3-1", "meetingId": "demo-3", "text": "Advance Emily Brown to final culture fit round.", "decidedBy": "Raj Patel", "rationale": "High technical competence in frontend and backend APIs.", "quote": "strong candidate feedback", "startSec": 80, "verified": True, "confidence": 0.96}
        ],
        "tasks": [
            {"id": "t3-1", "meetingId": "demo-3", "title": "Submit written technical evaluation and interview feedback", "owner": "Raj Patel", "deadline": "2026-10-06", "deadlineRaw": "by Monday", "deadlineAmbiguous": False, "priority": "high", "status": "done", "quote": "submit candidate debrief", "startSec": 80, "verified": True, "confidence": 0.92}
        ],
        "criticLog": [],
        "analytics": {
            "meetingId": "demo-3",
            "talkTime": [
                {"speakerId": "s1c", "speakerLabel": "Raj Patel", "seconds": 210, "percentage": 42.8},
                {"speakerId": "s2c", "speakerLabel": "Emily Brown", "seconds": 280, "percentage": 57.2}
            ],
            "avgTurnLength": 24.5,
            "interruptions": 0,
            "questionsAsked": 5,
            "healthScore": 92
        },
        "chatMessages": []
    }

    return [meeting1, meeting2, meeting3]


def get_initial_llm_calls() -> List[Dict[str, Any]]:
    """Seed LLM call history for the 3 models."""
    return [
        {"id": "call-1", "meetingId": "demo-1", "task": "transcription", "model": "gpt-4o-transcribe-diarize", "deployment": "openai-cloud", "tokensIn": 3200, "tokensOut": 1400, "costUsd": 0.0210, "latencyMs": 1420, "cached": False, "createdAt": "2026-10-04T10:01:00Z"},
        {"id": "call-2", "meetingId": "demo-1", "task": "embeddings", "model": "text-embedding-3-small", "deployment": "openai-cloud", "tokensIn": 1850, "tokensOut": 0, "costUsd": 0.00037, "latencyMs": 110, "cached": False, "createdAt": "2026-10-04T10:02:15Z"},
        {"id": "call-3", "meetingId": "demo-1", "task": "summarizer", "model": "gpt-4.1-mini", "deployment": "openai-cloud", "tokensIn": 2400, "tokensOut": 680, "costUsd": 0.0076, "latencyMs": 780, "cached": False, "createdAt": "2026-10-04T10:02:40Z"},
        {"id": "call-4", "meetingId": "demo-1", "task": "critic", "model": "gpt-4.1-mini", "deployment": "openai-cloud", "tokensIn": 1900, "tokensOut": 320, "costUsd": 0.0048, "latencyMs": 590, "cached": False, "createdAt": "2026-10-04T10:03:10Z"},
        {"id": "call-5", "meetingId": "demo-2", "task": "transcription", "model": "gpt-4o-transcribe-diarize", "deployment": "openai-cloud", "tokensIn": 2800, "tokensOut": 950, "costUsd": 0.0165, "latencyMs": 1280, "cached": False, "createdAt": "2026-09-26T14:02:00Z"},
        {"id": "call-6", "meetingId": "demo-2", "task": "embeddings", "model": "text-embedding-3-small", "deployment": "openai-cloud", "tokensIn": 1420, "tokensOut": 0, "costUsd": 0.00028, "latencyMs": 95, "cached": False, "createdAt": "2026-09-26T14:03:00Z"},
        {"id": "call-7", "meetingId": "demo-2", "task": "summarizer", "model": "gpt-4.1-mini", "deployment": "openai-cloud", "tokensIn": 2100, "tokensOut": 550, "costUsd": 0.0064, "latencyMs": 640, "cached": False, "createdAt": "2026-09-26T14:03:30Z"},
        {"id": "call-8", "meetingId": "demo-3", "task": "embeddings", "model": "text-embedding-3-small", "deployment": "openai-cloud", "tokensIn": 1150, "tokensOut": 0, "costUsd": 0.00023, "latencyMs": 85, "cached": False, "createdAt": "2026-09-30T11:01:00Z"},
        {"id": "call-9", "meetingId": "demo-3", "task": "summarizer", "model": "gpt-4.1-mini", "deployment": "openai-cloud", "tokensIn": 1600, "tokensOut": 480, "costUsd": 0.0052, "latencyMs": 520, "cached": False, "createdAt": "2026-09-30T11:01:45Z"},
    ]
