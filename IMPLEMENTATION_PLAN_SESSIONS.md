# Implementation Plan: Student Test-Taking with Real-Time Monitoring

## Overview

This document outlines the implementation plan for adding student test-taking functionality with real-time monitoring to the IELTS teaching FastAPI application. The feature allows teachers to create classes, start exercise sessions, and monitor students in real-time as they take tests.

## Business Requirements

### Core Features
1. **Teaching Classes**: Create and manage classes (e.g., "Beacon 31") with enrolled students
2. **Exercise Sessions**: Schedule and run test sessions where students take tests together
3. **Real-Time Monitoring**: Track student activities during tests:
   - Tab switching violations
   - Text highlighting (full detail: text, timestamps, positions)
   - Current test progress (passage/question position)
   - Answer submissions
4. **Global Timer**: All students see the same countdown (late joiners get less time)
5. **Reconnection Support**: Students can disconnect and reconnect without losing progress
6. **Event-Driven Updates**: WebSocket events only on actions (no periodic broadcasts)

### User Flow
1. Teacher creates a class (e.g., "Beacon 31") and enrolls students
2. Teacher creates a session scheduled for specific time (e.g., Monday 8PM)
3. At session time, teacher opens waiting room
4. Students join via WebSocket using their credentials
5. Teacher starts session → countdown begins for all connected students
6. Students take test while system monitors their activities
7. Students can disconnect and reconnect (state syncs from database)
8. Session completes when time expires or teacher force-completes
9. Teacher views session statistics and student performance

---

## Architecture Overview

### Design Principles
- **Clean Architecture**: Domain → Application → Infrastructure → Presentation
- **DDD (Domain-Driven Design)**: Aggregates, entities, value objects
- **CQRS Pattern**: Separate commands (write) and queries (read)
- **Repository Pattern**: Abstract data access with interfaces
- **Event-Driven**: WebSocket for real-time communication

### New Aggregates

#### 1. Class Aggregate
- **Purpose**: Represents teaching classes with enrolled students
- **Location**: `app/domain/aggregates/class/`
- **Status**: ACTIVE, ARCHIVED

#### 2. Session Aggregate
- **Purpose**: Manages exercise session lifecycle and participants
- **Location**: `app/domain/aggregates/session/`
- **Status**: SCHEDULED → WAITING_FOR_STUDENTS → IN_PROGRESS → COMPLETED (or CANCELLED)

#### 3. Enhanced Attempt Aggregate
- **Purpose**: Tracks individual student test attempts (already exists, needs enhancement)
- **Location**: `app/domain/aggregates/attempt/`
- **Enhancement**: Add text highlighting tracking

### Aggregate Relationships
```
Class (1) ─── (N) Session
Session (1) ─── (N) SessionParticipant (Value Object)
SessionParticipant ─── (1) Attempt
Attempt ─── (1) Test
```

All relationships use ID references (not embedding) to maintain aggregate boundaries.

---

## Implementation Phases

### Phase 1: Domain Layer (Start Here)

#### 1.1 Class Aggregate
**Directory**: `app/domain/aggregates/class/`

**Files to Create**:
- `__init__.py`
- `class_status.py` - Enum: ACTIVE, ARCHIVED
- `class.py` - Class aggregate root

**Class Aggregate Fields**:
```python
id: str
name: str (e.g., "Beacon 31")
description: Optional[str]
teacher_id: str  # Reference to User (ADMIN)
student_ids: List[str]  # References to Users (STUDENT)
status: ClassStatus
created_at: datetime
updated_at: Optional[datetime]
```

**Business Methods**:
- `enroll_student(student_id: str)` - Add student, check for duplicates
- `remove_student(student_id: str)` - Remove student, validate exists
- `archive()` - Change status to ARCHIVED

**Business Rules**:
- Student can only be enrolled once
- Cannot have duplicate student IDs
- Must validate teacher_id is ADMIN role (in use case layer)

---

#### 1.2 Session Aggregate
**Directory**: `app/domain/aggregates/session/`

**Files to Create**:
- `__init__.py`
- `session_status.py` - Enum: SCHEDULED, WAITING_FOR_STUDENTS, IN_PROGRESS, COMPLETED, CANCELLED
- `session_participant.py` - SessionParticipant value object
- `session.py` - Session aggregate root

**Session Aggregate Fields**:
```python
id: str
class_id: str  # Reference to Class
test_id: str  # Reference to Test
title: str
scheduled_at: datetime
started_at: Optional[datetime]
completed_at: Optional[datetime]
status: SessionStatus
participants: List[SessionParticipant]  # Value objects
created_by: str  # Teacher ID
created_at: datetime
updated_at: Optional[datetime]
```

**SessionParticipant Value Object Fields**:
```python
student_id: str
attempt_id: Optional[str]  # Links to Attempt aggregate
joined_at: Optional[datetime]
connection_status: str  # "CONNECTED" or "DISCONNECTED"
last_activity: Optional[datetime]
```

**Business Methods**:
- `start_waiting_phase()` - Open waiting room (SCHEDULED → WAITING_FOR_STUDENTS)
- `student_join(student_id: str)` - Student joins or reconnects
- `student_disconnect(student_id: str)` - Mark as disconnected
- `start_session() -> List[str]` - Start countdown, return connected student IDs (WAITING_FOR_STUDENTS → IN_PROGRESS)
- `link_attempt(student_id: str, attempt_id: str)` - Link created attempt to participant
- `complete_session()` - Mark as completed (IN_PROGRESS → COMPLETED)
- `cancel_session()` - Cancel before start (SCHEDULED/WAITING_FOR_STUDENTS → CANCELLED)

**Business Rules**:
- Can only start if at least one student connected
- Cannot modify once IN_PROGRESS
- Can only cancel if not IN_PROGRESS
- Students can join during WAITING_FOR_STUDENTS or IN_PROGRESS
- Global timer: started_at determines test end time for all students

---

#### 1.3 Enhanced Attempt Aggregate
**Directory**: `app/domain/aggregates/attempt/`

**Files to Modify**:
- `attempt.py` - Add new fields and methods

**Files to Create**:
- `text_highlight.py` - TextHighlight value object

**New Fields to Add**:
```python
highlighted_text: List[TextHighlight] = Field(default_factory=list)
```

**TextHighlight Value Object Fields**:
```python
timestamp: datetime
text: str  # The actual highlighted text
passage_id: str
position_start: int  # Character position in passage
position_end: int
```

**New Methods to Add**:
```python
record_tab_violation(violation_type: str = "TAB_SWITCH") -> None
record_text_highlight(text: str, passage_id: str, start: int, end: int) -> None
update_progress(passage_index: int, question_index: int) -> None
submit_answer(answer: Answer) -> None  # Update or add answer
update_time_remaining(seconds: int) -> None
submit_attempt() -> None  # Mark as SUBMITTED
abandon_attempt() -> None  # Mark as ABANDONED
```

---

#### 1.4 Repository Interfaces
**Directory**: `app/domain/repositories/`

**Files to Create**:

1. **`class_repository.py`**:
```python
class ClassRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, class_entity: Class) -> Class

    @abstractmethod
    async def get_by_id(self, class_id: str) -> Optional[Class]

    @abstractmethod
    async def get_all(self, teacher_id: Optional[str] = None) -> List[Class]

    @abstractmethod
    async def update(self, class_entity: Class) -> Class

    @abstractmethod
    async def delete(self, class_id: str) -> None
```

2. **`session_repository.py`**:
```python
class SessionRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, session: Session) -> Session

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[Session]

    @abstractmethod
    async def get_by_class(self, class_id: str) -> List[Session]

    @abstractmethod
    async def get_by_student(self, student_id: str) -> List[Session]

    @abstractmethod
    async def update(self, session: Session) -> Session

    @abstractmethod
    async def delete(self, session_id: str) -> None
```

3. **`attempt_repository.py`** (NEW):
```python
class AttemptRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, attempt: Attempt) -> Attempt

    @abstractmethod
    async def get_by_id(self, attempt_id: str) -> Optional[Attempt]

    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[Attempt]

    @abstractmethod
    async def update(self, attempt: Attempt) -> Attempt

    @abstractmethod
    async def delete(self, attempt_id: str) -> None
```

---

#### 1.5 Domain Errors
**Directory**: `app/domain/errors/`

**Files to Create**:

1. **`class_errors.py`**:
```python
- ClassNotFoundError
- StudentAlreadyEnrolledError
- StudentNotInClassError
- ClassAlreadyArchivedError
- InvalidClassStatusError
```

2. **`session_errors.py`**:
```python
- SessionNotFoundError
- InvalidSessionStatusError
- SessionNotJoinableError
- NoStudentsConnectedError
- CannotCancelActiveSessionError
- StudentNotInSessionError
```

3. **`attempt_errors.py`**:
```python
- AttemptNotFoundError
- InvalidAttemptStatusError
- AttemptAlreadySubmittedError
```

---

### Phase 2: Infrastructure Layer

#### 2.1 Database Models
**Directory**: `app/infrastructure/persistence/models/`

**Files to Create**:

1. **`class_model.py`**:
```python
class ClassModel(Base):
    __tablename__ = "classes"

    id: str (PK)
    name: str
    description: str (nullable)
    teacher_id: str (FK to users)
    student_ids: JSON  # List of student IDs
    status: str
    created_at: datetime
    updated_at: datetime (nullable)

    # Relationships
    teacher = relationship("UserModel")
    sessions = relationship("SessionModel", back_populates="class_entity")
```

2. **`session_model.py`**:
```python
class SessionModel(Base):
    __tablename__ = "sessions"

    id: str (PK)
    class_id: str (FK to classes)
    test_id: str (FK to tests)
    title: str
    scheduled_at: datetime
    started_at: datetime (nullable)
    completed_at: datetime (nullable)
    status: str
    participants: JSON  # List of SessionParticipant dicts
    created_by: str (FK to users)
    created_at: datetime
    updated_at: datetime (nullable)

    # Relationships
    class_entity = relationship("ClassModel", back_populates="sessions")
    test = relationship("TestModel")
    creator = relationship("UserModel")
```

3. **Update `attempt_model.py`**:
```python
# Add new column:
highlighted_text: JSON  # List of TextHighlight dicts
session_id: str (FK to sessions, nullable)  # Link to session
```

**Files to Modify**:
- Update `app/infrastructure/persistence/models/__init__.py` to export new models

---

#### 2.2 Database Migration
**Directory**: `migrations/versions/`

**Create Alembic Migration**:
```bash
alembic revision --autogenerate -m "Add classes, sessions, and update attempts for session support"
```

**Migration should**:
- Create `classes` table
- Create `sessions` table
- Add `highlighted_text` column to `attempts` table (JSON type)
- Add `session_id` column to `attempts` table (FK, nullable)
- Create indexes on:
  - `classes.teacher_id`
  - `sessions.class_id`
  - `sessions.status`
  - `attempts.session_id`

---

#### 2.3 Repository Implementations
**Directory**: `app/infrastructure/repositories/`

**Files to Create**:

1. **`sql_class_repository.py`** - Implements `ClassRepositoryInterface`
2. **`sql_session_repository.py`** - Implements `SessionRepositoryInterface`
3. **`sql_attempt_repository.py`** - Implements `AttemptRepositoryInterface`

**Key Implementation Notes**:
- Convert between ORM models and domain entities using `to_domain()` pattern
- Handle JSON serialization/deserialization for lists (student_ids, participants, highlighted_text)
- Use SQLAlchemy async session
- Implement proper error handling

---

#### 2.4 WebSocket Infrastructure
**Directory**: `app/infrastructure/websocket/`

**Files to Create**:

1. **`session_connection_manager.py`**:
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Structure: {session_id: {user_id: WebSocket}}

    async def connect(session_id: str, user_id: str, websocket: WebSocket)
    def disconnect(session_id: str, user_id: str)
    async def broadcast_to_session(session_id: str, message: dict)
    async def send_to_teacher(session_id: str, teacher_id: str, message: dict)
    async def send_to_student(session_id: str, student_id: str, message: dict)
```

2. **`event_types.py`**:
```python
class WSEventType(str, Enum):
    # Teacher events
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    STUDENT_JOINED = "student_joined"
    STUDENT_LEFT = "student_left"

    # Student events
    ANSWER_SUBMITTED = "answer_submitted"
    TAB_VIOLATION = "tab_violation"
    TEXT_HIGHLIGHTED = "text_highlighted"
    PROGRESS_UPDATE = "progress_update"

    # Monitoring (to teacher)
    STUDENT_STATUS_UPDATE = "student_status_update"
    REAL_TIME_STATS = "real_time_stats"

    # State sync
    STATE_SYNC_REQUEST = "state_sync_request"
    STATE_SYNC_RESPONSE = "state_sync_response"
```

3. **`__init__.py`** - Export ConnectionManager and WSEventType

---

### Phase 3: Application Layer

#### 3.1 Class Use Cases
**Directory**: `app/application/use_cases/classes/`

**Commands** (`commands/`):
1. `create_class/` - CreateClassUseCase (Admin only)
   - Validate teacher_id is ADMIN role
   - Create Class aggregate
   - Persist via repository

2. `update_class/` - UpdateClassUseCase (Admin only)
   - Update name, description
   - Validate ownership

3. `archive_class/` - ArchiveClassUseCase (Admin only)
   - Call class.archive()
   - Validate no active sessions

4. `enroll_student/` - EnrollStudentUseCase (Admin only)
   - Validate student exists and has STUDENT role
   - Call class.enroll_student()

5. `remove_student/` - RemoveStudentUseCase (Admin only)
   - Call class.remove_student()

**Queries** (`queries/`):
1. `get_class_by_id/` - GetClassByIdUseCase
2. `get_all_classes/` - GetAllClassesUseCase (filter by teacher)

---

#### 3.2 Session Use Cases
**Directory**: `app/application/use_cases/sessions/`

**Commands** (`commands/`):
1. `create_session/` - CreateSessionUseCase (Admin only)
   - Validate class exists and teacher owns it
   - Validate test exists
   - Create Session aggregate
   - Initialize participants from class.student_ids

2. `start_waiting_phase/` - StartWaitingPhaseUseCase (Admin only)
   - Call session.start_waiting_phase()
   - Broadcast SESSION_WAITING event via WebSocket

3. `start_session/` - StartSessionUseCase (Admin only)
   - Call session.start_session() → get connected student IDs
   - For each connected student:
     - Create Attempt (test_id, student_id, session_id)
     - Call session.link_attempt(student_id, attempt_id)
   - Calculate end_time from test.time_limit
   - Broadcast SESSION_STARTED with end_time

4. `complete_session/` - CompleteSessionUseCase (Admin only)
   - Call session.complete_session()
   - Broadcast SESSION_COMPLETED

5. `cancel_session/` - CancelSessionUseCase (Admin only)
   - Call session.cancel_session()

6. `student_join_session/` - StudentJoinSessionUseCase (Student)
   - Validate student in class
   - Call session.student_join(student_id)
   - If session IN_PROGRESS and no attempt exists, create attempt
   - Broadcast STUDENT_JOINED to teacher

**Queries** (`queries/`):
1. `get_session_by_id/` - GetSessionByIdUseCase
2. `get_my_sessions/` - GetMySessionsUseCase (Student)
   - Find sessions where student_id in session.participants
3. `get_session_stats/` - GetSessionStatsUseCase (Teacher)
   - Aggregate stats from all attempts in session

---

#### 3.3 Attempt Use Cases
**Directory**: `app/application/use_cases/attempts/`

**Commands** (`commands/`):
1. `create_attempt/` - CreateAttemptUseCase (internal, called by start_session)

2. `submit_answer/` - SubmitAnswerUseCase (Student)
   - Validate student owns attempt
   - Call attempt.submit_answer()
   - Persist immediately
   - Broadcast ANSWER_SUBMITTED to teacher

3. `record_tab_violation/` - RecordTabViolationUseCase (Student)
   - Call attempt.record_tab_violation()
   - Persist immediately
   - Broadcast TAB_VIOLATION to teacher

4. `record_text_highlight/` - RecordTextHighlightUseCase (Student)
   - Call attempt.record_text_highlight()
   - Persist immediately
   - Broadcast TEXT_HIGHLIGHTED to teacher

5. `update_progress/` - UpdateProgressUseCase (Student)
   - Call attempt.update_progress()
   - Persist immediately
   - Broadcast PROGRESS_UPDATE to teacher

6. `submit_attempt/` - SubmitAttemptUseCase (Student)
   - Call attempt.submit_attempt()
   - Calculate score
   - Persist
   - Broadcast to teacher

**Queries** (`queries/`):
1. `get_attempt_by_id/` - GetAttemptByIdUseCase (Student, for state sync)
2. `get_attempt_for_monitoring/` - GetAttemptForMonitoringUseCase (Teacher)

---

### Phase 4: Presentation Layer

#### 4.1 REST API Routers
**Directory**: `app/presentation/routes/`

**Files to Create**:

1. **`class_router.py`**:
```python
POST   /api/classes                         # CreateClass
GET    /api/classes                         # GetAllClasses
GET    /api/classes/{class_id}              # GetClassById
PUT    /api/classes/{class_id}              # UpdateClass
DELETE /api/classes/{class_id}              # ArchiveClass
POST   /api/classes/{class_id}/students     # EnrollStudent
DELETE /api/classes/{class_id}/students/{student_id}  # RemoveStudent
```

2. **`session_router.py`**:
```python
POST   /api/sessions                        # CreateSession
GET    /api/sessions                        # GetAllSessions (Admin)
GET    /api/sessions/my-sessions            # GetMySessions (Student)
GET    /api/sessions/{session_id}           # GetSessionById
POST   /api/sessions/{session_id}/start-waiting  # StartWaitingPhase
POST   /api/sessions/{session_id}/start     # StartSession
POST   /api/sessions/{session_id}/complete  # CompleteSession
DELETE /api/sessions/{session_id}           # CancelSession
GET    /api/sessions/{session_id}/stats     # GetSessionStats
```

3. **`attempt_router.py`**:
```python
GET    /api/attempts/{attempt_id}           # GetAttemptById
POST   /api/attempts/{attempt_id}/answers   # SubmitAnswer
POST   /api/attempts/{attempt_id}/submit    # SubmitAttempt
```

---

#### 4.2 WebSocket Endpoint
**Directory**: `app/presentation/websocket/`

**Files to Create**:

1. **`session_websocket.py`**:
```python
@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    # 1. Authenticate JWT token
    # 2. Get user_id and role from token
    # 3. Validate user has access to session
    # 4. Connect to manager
    # 5. Call student_join_session use case
    # 6. Listen for messages and route to event processor
    # 7. Handle disconnect
```

2. **`event_processor.py`**:
```python
async def process_websocket_event(
    session_id: str,
    user_id: str,
    event: dict,
    manager: ConnectionManager,
    # ... use cases injected
):
    event_type = event["type"]
    data = event["data"]

    # Route to appropriate use case based on event_type
    if event_type == "answer_submitted":
        await submit_answer_use_case.execute(...)
        await manager.send_to_teacher(...)
    elif event_type == "tab_violation":
        await record_tab_violation_use_case.execute(...)
        await manager.send_to_teacher(...)
    # ... etc
```

3. **`__init__.py`** - Export router

---

#### 4.3 Dependency Injection
**File to Modify**: `app/container.py`

**Add**:
```python
# Repositories
class_repository = providers.Factory(SQLClassRepository)
session_repository = providers.Factory(SQLSessionRepository)
attempt_repository = providers.Factory(SQLAttemptRepository)

# WebSocket
connection_manager = providers.Singleton(ConnectionManager)

# Class Use Cases
create_class_use_case = providers.Factory(CreateClassUseCase, ...)
# ... all class_ use cases

# Session Use Cases
create_session_use_case = providers.Factory(CreateSessionUseCase, ...)
# ... all session use cases

# Attempt Use Cases
submit_answer_use_case = providers.Factory(SubmitAnswerUseCase, ...)
# ... all attempt use cases
```

**Create Dependency Functions**:
```python
async def get_class_use_cases(session: AsyncSession = Depends(get_database_session)):
    # Create and return ClassUseCases dataclass

async def get_session_use_cases(session: AsyncSession = Depends(get_database_session)):
    # Create and return SessionUseCases dataclass

async def get_attempt_use_cases(session: AsyncSession = Depends(get_database_session)):
    # Create and return AttemptUseCases dataclass

def get_connection_manager() -> ConnectionManager:
    return container.connection_manager()
```

---

#### 4.4 Main App Integration
**File to Modify**: `app/main.py` (or wherever FastAPI app is initialized)

**Add**:
```python
from app.presentation.routes.class_router import router as class_router
from app.presentation.routes.session_router import router as session_router
from app.presentation.routes.attempt_router import router as attempt_router
from app.presentation.websocket.session_websocket import router as ws_router

app.include_router(class_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(attempt_router, prefix="/api")
app.include_router(ws_router)  # WebSocket routes
```

---

### Phase 5: Testing & Verification

#### 5.1 Unit Tests
**Directory**: `tests/domain/`

Create tests for:
- `test_class_aggregate.py` - Test business rules
- `test_session_aggregate.py` - Test state transitions
- `test_attempt_aggregate.py` - Test new methods

#### 5.2 Integration Tests
**Directory**: `tests/integration/`

Create tests for:
- Repository implementations
- Use case flows
- WebSocket connection handling

#### 5.3 End-to-End Test
**Manual Test Flow**:
1. Start server: `uvicorn app.main:app --reload`
2. Register admin and student users
3. Create class via API
4. Enroll students in class
5. Create session for class
6. Open waiting room
7. Connect students via WebSocket
8. Start session
9. Submit answers, trigger violations
10. Disconnect/reconnect student (verify state sync)
11. Complete session
12. View session statistics

---

## Database Schema

### Tables

#### `classes`
```sql
id VARCHAR(36) PK
name VARCHAR(100) NOT NULL
description TEXT
teacher_id VARCHAR(36) FK(users.id) NOT NULL
student_ids JSON NOT NULL  -- Array of user IDs
status VARCHAR(20) NOT NULL  -- ACTIVE, ARCHIVED
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP
```

#### `sessions`
```sql
id VARCHAR(36) PK
class_id VARCHAR(36) FK(classes.id) NOT NULL
test_id VARCHAR(36) FK(tests.id) NOT NULL
title VARCHAR(200) NOT NULL
scheduled_at TIMESTAMP NOT NULL
started_at TIMESTAMP
completed_at TIMESTAMP
status VARCHAR(30) NOT NULL  -- SCHEDULED, WAITING_FOR_STUDENTS, IN_PROGRESS, COMPLETED, CANCELLED
participants JSON NOT NULL  -- Array of SessionParticipant objects
created_by VARCHAR(36) FK(users.id) NOT NULL
created_at TIMESTAMP NOT NULL
updated_at TIMESTAMP
```

#### `attempts` (updated)
```sql
... existing columns ...
highlighted_text JSON  -- Array of TextHighlight objects
session_id VARCHAR(36) FK(sessions.id)  -- NULL for standalone attempts
```

### Indexes
```sql
CREATE INDEX idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX idx_sessions_class_id ON sessions(class_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_attempts_session_id ON attempts(session_id);
```

---

## API Endpoints Summary

### Authentication
All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Class Management (Admin Only)
- `POST /api/classes` - Create class
- `GET /api/classes` - List classes
- `GET /api/classes/{class_id}` - Get class details
- `PUT /api/classes/{class_id}` - Update class
- `DELETE /api/classes/{class_id}` - Archive class
- `POST /api/classes/{class_id}/students` - Enroll student
- `DELETE /api/classes/{class_id}/students/{student_id}` - Remove student

### Session Management
- `POST /api/sessions` - Create session (Admin)
- `GET /api/sessions` - List sessions (Admin)
- `GET /api/sessions/my-sessions` - Get student's sessions (Student)
- `GET /api/sessions/{session_id}` - Get session details
- `POST /api/sessions/{session_id}/start-waiting` - Open waiting room (Admin)
- `POST /api/sessions/{session_id}/start` - Start countdown (Admin)
- `POST /api/sessions/{session_id}/complete` - Force complete (Admin)
- `DELETE /api/sessions/{session_id}` - Cancel session (Admin)
- `GET /api/sessions/{session_id}/stats` - Get statistics (Teacher)

### Attempt Management
- `GET /api/attempts/{attempt_id}` - Get attempt state (Student)
- `POST /api/attempts/{attempt_id}/answers` - Submit answer (Student)
- `POST /api/attempts/{attempt_id}/submit` - Submit final attempt (Student)

### WebSocket
- `WS /ws/sessions/{session_id}?token=<jwt>` - Connect to session

---

## WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${sessionId}?token=${jwtToken}`);
```

### Message Format
All messages are JSON:

#### Client → Server
```json
{
  "type": "answer_submitted",
  "data": {
    "question_id": "q123",
    "answer": "A"
  }
}
```

#### Server → Client
```json
{
  "type": "student_joined",
  "data": {
    "student_id": "s456",
    "student_name": "John Doe",
    "joined_at": "2024-01-10T12:00:00Z"
  }
}
```

### Event Types

#### From Student
- `answer_submitted` - Student submitted/updated an answer
- `tab_violation` - Student switched tabs
- `text_highlighted` - Student highlighted text
- `progress_update` - Student moved to different question
- `state_sync_request` - Request full state (after reconnect)

#### From Server (to Student)
- `session_started` - Session countdown started
- `session_completed` - Session finished
- `state_sync_response` - Full state response

#### From Server (to Teacher)
- `student_joined` - Student connected
- `student_left` - Student disconnected
- `student_status_update` - Student activity update
- `real_time_stats` - Aggregated session statistics

---

## Security Considerations

### Authentication
- JWT tokens required for all API and WebSocket connections
- Token validation on WebSocket connect
- User role verification (ADMIN vs STUDENT)

### Authorization
- Students can only access their own attempts
- Teachers can only manage their own classes/sessions
- Teachers can only monitor sessions from their classes
- Admins have full access

### Data Validation
- All WebSocket messages validated against schemas
- Server-side validation for all actions
- Rate limiting on WebSocket messages

### Cheating Prevention
- Server-authoritative timer (cannot be manipulated client-side)
- All answers validated and scored server-side
- Tab violations tracked
- Full activity audit trail

---

## Performance Considerations

### Optimization Strategies
1. **Event-Driven**: Only send WebSocket messages on actions (no periodic broadcasts)
2. **Immediate Persistence**: Critical data saved immediately to database
3. **Eager Loading**: Use SQLAlchemy `selectinload` for related data
4. **Indexes**: Database indexes on foreign keys and status fields
5. **Connection Pooling**: Use FastAPI/SQLAlchemy connection pooling

### Scalability (Future)
- Redis pub/sub for multi-instance WebSocket support
- Session state caching in Redis
- Batch operations for highlights (if volume high)
- Database read replicas for monitoring queries

---

## Deployment Checklist

### Database
- [ ] Run Alembic migration: `alembic upgrade head`
- [ ] Verify tables created: `classes`, `sessions`
- [ ] Verify indexes created
- [ ] Verify `attempts` table updated

### Application
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Update environment variables if needed
- [ ] Start server: `uvicorn app.main:app --reload`
- [ ] Test health endpoint

### Testing
- [ ] Run unit tests: `pytest tests/domain/`
- [ ] Run integration tests: `pytest tests/integration/`
- [ ] Manual E2E test (see Phase 5.3)
- [ ] WebSocket connection test
- [ ] Load test with multiple concurrent sessions

### Monitoring
- [ ] Set up logging for WebSocket connections
- [ ] Monitor database connection pool
- [ ] Set up alerts for failed sessions
- [ ] Track WebSocket disconnect rate

---

## Troubleshooting

### Common Issues

**Issue**: WebSocket connection fails
- Check JWT token is valid
- Verify user has access to session
- Check CORS settings for WebSocket

**Issue**: State not syncing after reconnect
- Verify attempt_id is correct
- Check database has latest data
- Ensure STATE_SYNC_RESPONSE includes all fields

**Issue**: Global timer out of sync
- Verify server time is accurate (use NTP)
- Check started_at timestamp in session
- Calculate remaining time server-side, not client-side

**Issue**: Students can't join session
- Verify session status is WAITING_FOR_STUDENTS or IN_PROGRESS
- Check student is enrolled in class
- Verify class_id → session relationship

---

## Next Steps

### Phase 1 - Domain Layer (Week 1)
Start with:
1. Create Class aggregate and status enum
2. Create Session aggregate with participant VO
3. Update Attempt aggregate
4. Define repository interfaces
5. Create domain errors

### Phase 2 - Infrastructure (Week 2)
1. Create SQLAlchemy models
2. Run database migration
3. Implement repositories
4. Create WebSocket infrastructure

### Phase 3 - Application (Week 3)
1. Implement Class use cases
2. Implement Session use cases
3. Implement Attempt use cases

### Phase 4 - Presentation (Week 4)
1. Create REST API routers
2. Implement WebSocket endpoint
3. Update dependency injection
4. Integrate with main app

### Phase 5 - Testing (Week 5)
1. Write unit tests
2. Write integration tests
3. Perform E2E testing
4. Load testing

---

## Questions or Clarifications

If you have questions during implementation:
1. Refer to existing aggregates (Test, Passage) for patterns
2. Check the plan file: `/Users/henrynguyen/.claude/plans/reflective-orbiting-ullman.md`
3. Review existing use cases for CQRS patterns
4. Consult FastAPI WebSocket documentation for connection handling

---

## Summary

This implementation adds a complete student test-taking system with real-time monitoring to your IELTS teaching application. The design follows clean architecture and DDD principles, maintains consistency with your existing codebase, and provides a robust, scalable foundation for live test sessions.

Key features:
- ✅ Teaching classes with student enrollment
- ✅ Scheduled exercise sessions
- ✅ Global timer for synchronized testing
- ✅ Real-time monitoring (tab switches, highlights, progress, answers)
- ✅ WebSocket-based communication
- ✅ Reconnection support with state sync
- ✅ Event-driven updates (no polling)
- ✅ Server-authoritative validation
- ✅ Full audit trail

The implementation is broken into 5 clear phases, with each phase building on the previous one, making it easy to implement incrementally and test as you go.
