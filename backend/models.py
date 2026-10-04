"""
Data models and type definitions for Meeting Studio.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import time
import uuid

def uid() -> str:
    return uuid.uuid4().hex[:10]

@dataclass
class Speaker:
    id: str
    label: str
    displayName: str
    role: str = ""
    suggestedName: Optional[str] = None
    speakerSource: str = "model"  # 'model' | 'inferred'
    color: str = "#2563eb"

@dataclass
class Segment:
    id: str
    meetingId: str
    idx: number if False else int
    speakerId: str
    speakerLabel: str
    startSec: float
    endSec: float
    text: str
    textRedacted: Optional[str] = None
    sentiment: str = "neutral"  # 'positive' | 'neutral' | 'negative'
    embedding: Optional[List[float]] = None

@dataclass
class DetailedTopic:
    topic: str
    text: str
    startSec: float

@dataclass
class Summary:
    meetingId: str
    tldr: str
    oneMinute: str
    detailed: List[Dict[str, Any]] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    outputLanguage: str = "en"

@dataclass
class Insight:
    id: str
    meetingId: str
    kind: str  # 'insight' | 'risk' | 'blocker' | 'opportunity' | 'open_question'
    text: str
    quote: str
    startSec: float
    confidence: float = 0.9

@dataclass
class Decision:
    id: str
    meetingId: str
    text: str
    decidedBy: str
    rationale: str
    quote: str
    startSec: float
    verified: bool = True
    confidence: float = 0.95

@dataclass
class Task:
    id: str
    meetingId: str
    title: str
    owner: str
    deadline: Optional[str] = None
    deadlineRaw: str = ""
    deadlineAmbiguous: bool = False
    priority: str = "medium"  # 'low' | 'medium' | 'high'
    status: str = "todo"      # 'todo' | 'doing' | 'done'
    quote: str = ""
    startSec: float = 0.0
    verified: bool = True
    confidence: float = 0.9
    createdAt: str = ""
    updatedAt: str = ""

@dataclass
class CriticLogEntry:
    id: str
    meetingId: str
    itemType: str  # 'task' | 'decision'
    itemRef: str
    action: str    # 'kept' | 'removed' | 'corrected'
    reason: str

@dataclass
class ConflictEvidence:
    meeting: str
    quote: str
    date: str

@dataclass
class Conflict:
    id: str
    meetingId: str
    otherMeetingId: str
    otherMeetingTitle: str
    kind: str  # 'contradiction' | 'commitment'
    description: str
    evidence: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class ChatMessage:
    id: str
    meetingId: Optional[str]
    role: str  # 'user' | 'assistant'
    content: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    createdAt: str = ""

@dataclass
class LLMCall:
    id: str
    meetingId: Optional[str]
    task: str  # 'transcription', 'embeddings', 'summarizer', 'critic', 'rag_answer'
    model: str # 'gpt-4o-transcribe-diarize' | 'text-embedding-3-small' | 'gpt-4.1-mini'
    deployment: str
    tokensIn: int
    tokensOut: int
    costUsd: float
    latencyMs: int
    cached: bool = False
    createdAt: str = ""

@dataclass
class Meeting:
    id: str
    title: str
    meetingDate: str
    sourceFilename: str
    mediaType: str = "audio"  # 'audio' | 'video' | 'transcript'
    durationSec: float = 0.0
    language: str = "en"
    meetingType: str = "planning"  # 'standup' | 'client_call' | 'interview' | 'brainstorm' | 'retro' | 'planning' | 'general'
    status: str = "done"  # 'queued' | 'transcribing' | 'speakers' | 'analyzing' | 'verifying' | 'indexing' | 'done' | 'failed'
    statusDetail: str = "Processing complete"
    progressPct: int = 100
    confidentialMode: bool = False
    healthScore: Optional[int] = 80
    tags: List[str] = field(default_factory=list)
    createdAt: str = ""
    updatedAt: str = ""
    speakers: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    criticLog: List[Dict[str, Any]] = field(default_factory=list)
    analytics: Optional[Dict[str, Any]] = None
    chatMessages: List[Dict[str, Any]] = field(default_factory=list)
