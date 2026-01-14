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

---

# ADDENDUM: Session Management REST APIs + WebSocket Implementation

## Overview

This addendum details the implementation for 4 admin session management REST endpoints with real-time WebSocket broadcasting for efficient session state updates.

**New Endpoints to Implement:**
- `POST /api/v1/sessions/{session_id}/start-waiting` - Open waiting room (Admin/Teacher)
- `POST /api/v1/sessions/{session_id}/start` - Start countdown (Admin/Teacher)
- `POST /api/v1/sessions/{session_id}/complete` - Force complete (Admin/Teacher)
- `DELETE /api/v1/sessions/{session_id}` - Delete session (Admin only)

**New WebSocket Endpoint:**
- `WS /api/v1/sessions/{session_id}/ws` - Real-time session updates

## Architecture Decisions

### Permissions Strategy
- **State transitions** (start-waiting, start, complete): `RequireRoles([ADMIN, TEACHER])`
  - Teachers can manage sessions for their classes (validated: user teaches the class)
  - Admins have unrestricted access
- **DELETE**: Admin-only to prevent accidental data loss
- **IN_PROGRESS sessions**: Cannot be deleted (protect data integrity)

### WebSocket Architecture
- **Location**: `/app/infrastructure/websocket/` (infrastructure concern)
- **Broadcasting**: Direct calls from use cases (hybrid approach)
  - Use cases receive `ConnectionManager` via DI
  - Broadcast after successful domain operation + persistence
  - WebSocket is optional (no-op if no connections)
- **Authentication**: JWT token in query parameter
- **Auto-join**: Students auto-join session on WebSocket connect

### Integration Pattern
```
REST Endpoint → Use Case → Domain Method → Repository.update()
                    ↓
            ConnectionManager.broadcast() → All WebSocket clients
```

---

## Implementation Steps

### Step 1: Domain Layer - Add New Errors

**File**: `/app/domain/errors/session_errors.py`

Add two new error classes:

```python
class NoPermissionToManageSessionError(Error):
    """Raised when user doesn't have permission to manage a session"""
    def __init__(self, user_id: str, session_id: str):
        super().__init__(
            f"User {user_id} does not have permission to manage session {session_id}",
            ErrorCode.FORBIDDEN
        )

class CannotDeleteSessionError(Error):
    """Raised when trying to delete an IN_PROGRESS session"""
    def __init__(self, session_id: str):
        super().__init__(
            f"Cannot delete session {session_id}: session is currently IN_PROGRESS",
            ErrorCode.CONFLICT
        )
```

---

### Step 2: Infrastructure - WebSocket Components

#### 2.1 Create ConnectionManager

**File**: `/app/infrastructure/websocket/connection_manager.py`

```python
import asyncio
import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections grouped by session_id

    Responsibilities:
    - Track active connections per session
    - Broadcast messages to all clients in a session
    - Handle connection cleanup
    """

    def __init__(self):
        # Structure: {session_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, user_id: str, websocket: WebSocket):
        """Add a new WebSocket connection to a session"""
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = {}
            self.active_connections[session_id][user_id] = websocket
            logger.info(f"User {user_id} connected to session {session_id}")

    async def disconnect(self, session_id: str, user_id: str):
        """Remove a WebSocket connection from a session"""
        async with self._lock:
            if session_id in self.active_connections:
                if user_id in self.active_connections[session_id]:
                    del self.active_connections[session_id][user_id]
                    logger.info(f"User {user_id} disconnected from session {session_id}")

                # Clean up empty session
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connected clients in a session"""
        if session_id not in self.active_connections:
            return  # No one is listening - that's OK

        disconnected = []
        for user_id, websocket in self.active_connections[session_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to {user_id}: {e}")
                disconnected.append(user_id)

        # Cleanup failed connections
        for user_id in disconnected:
            await self.disconnect(session_id, user_id)

    async def send_personal_message(self, session_id: str, user_id: str, message: dict):
        """Send message to a specific user in a session"""
        if session_id not in self.active_connections:
            return

        if user_id not in self.active_connections[session_id]:
            return

        try:
            await self.active_connections[session_id][user_id].send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message to {user_id}: {e}")
            await self.disconnect(session_id, user_id)

    def get_connected_users(self, session_id: str) -> list[str]:
        """Get list of connected user IDs in a session"""
        if session_id not in self.active_connections:
            return []
        return list(self.active_connections[session_id].keys())

    def is_user_connected(self, session_id: str, user_id: str) -> bool:
        """Check if a user is connected to a session"""
        if session_id not in self.active_connections:
            return False
        return user_id in self.active_connections[session_id]
```

#### 2.2 Create Message Types

**File**: `/app/infrastructure/websocket/message_types.py`

```python
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel
from app.domain.aggregates.session.session_status import SessionStatus

# ===== Client → Server Messages =====

class HeartbeatMessage(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"

class DisconnectMessage(BaseModel):
    type: Literal["disconnect"] = "disconnect"
    reason: Optional[str] = None

# ===== Server → Client Messages =====

class ConnectedMessage(BaseModel):
    type: Literal["connected"] = "connected"
    session_id: str
    timestamp: datetime

class SessionStatusChangedMessage(BaseModel):
    type: Literal["session_status_changed"] = "session_status_changed"
    session_id: str
    status: SessionStatus
    timestamp: datetime

class ParticipantJoinedMessage(BaseModel):
    type: Literal["participant_joined"] = "participant_joined"
    session_id: str
    student_id: str
    connected_count: int
    timestamp: datetime

class ParticipantDisconnectedMessage(BaseModel):
    type: Literal["participant_disconnected"] = "participant_disconnected"
    session_id: str
    student_id: str
    connected_count: int
    timestamp: datetime

class WaitingRoomOpenedMessage(BaseModel):
    type: Literal["waiting_room_opened"] = "waiting_room_opened"
    session_id: str
    timestamp: datetime

class SessionStartedMessage(BaseModel):
    type: Literal["session_started"] = "session_started"
    session_id: str
    started_at: datetime
    connected_students: List[str]
    timestamp: datetime

class SessionCompletedMessage(BaseModel):
    type: Literal["session_completed"] = "session_completed"
    session_id: str
    completed_at: datetime
    timestamp: datetime

class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str
```

#### 2.3 WebSocket Authentication Helper

**File**: `/app/infrastructure/websocket/websocket_auth.py`

```python
from typing import Optional
from app.infrastructure.security.jwt_service import JwtService
from app.domain.aggregates.users.user import UserRole
from app.domain.aggregates.session.session import Session

async def validate_websocket_access(
    user_id: str,
    role: UserRole,
    session: Session,
    class_repo,
) -> bool:
    """
    Validate that a user has access to a session's WebSocket

    Rules:
    - Students: Must be participant in session
    - Teachers: Must teach the class
    - Admins: Always allowed
    """
    if role == UserRole.ADMIN:
        return True

    if role == UserRole.TEACHER:
        # Check if teacher teaches the class
        class_entity = await class_repo.get_by_id(session.class_id)
        if class_entity and user_id in class_entity.teacher_ids:
            return True
        return False

    if role == UserRole.STUDENT:
        # Check if student is participant
        return session.is_student_in_session(user_id)

    return False
```

#### 2.4 WebSocket Package Init

**File**: `/app/infrastructure/websocket/__init__.py`

```python
from .connection_manager import ConnectionManager
from .message_types import (
    ConnectedMessage,
    SessionStatusChangedMessage,
    ParticipantJoinedMessage,
    ParticipantDisconnectedMessage,
    WaitingRoomOpenedMessage,
    SessionStartedMessage,
    SessionCompletedMessage,
    ErrorMessage,
)

__all__ = [
    "ConnectionManager",
    "ConnectedMessage",
    "SessionStatusChangedMessage",
    "ParticipantJoinedMessage",
    "ParticipantDisconnectedMessage",
    "WaitingRoomOpenedMessage",
    "SessionStartedMessage",
    "SessionCompletedMessage",
    "ErrorMessage",
]
```

---

### Step 3: Application Layer - Use Cases

#### 3.1 Start Waiting Phase Use Case

**Directory**: `/app/application/use_cases/sessions/commands/start_waiting/`

**File**: `start_waiting_dto.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from app.domain.aggregates.session.session_status import SessionStatus

@dataclass
class StartWaitingPhaseRequest:
    session_id: str

@dataclass
class ParticipantDTO:
    student_id: str
    attempt_id: Optional[str]
    joined_at: Optional[datetime]
    connection_status: str
    last_activity: Optional[datetime]

@dataclass
class StartWaitingPhaseResponse:
    id: str
    class_id: str
    test_id: str
    title: str
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: SessionStatus
    participants: List[ParticipantDTO]
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
```

**File**: `start_waiting_use_case.py`

```python
from datetime import datetime, timezone
from app.application.use_cases.authenticated_use_case import AuthenticatedUseCase
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.session_errors import (
   SessionNotFoundError,
   NoPermissionToManageSessionError,
)
from app.domain.errors.class_errors import ClassNotFoundError
from app.infrastructure.web_socket import ConnectionManager, WaitingRoomOpenedMessage
from .start_waiting_dto import (
   StartWaitingPhaseRequest,
   StartWaitingPhaseResponse,
   ParticipantDTO,
)


class StartWaitingPhaseUseCase(
   AuthenticatedUseCase[StartWaitingPhaseRequest, StartWaitingPhaseResponse]
):
   def __init__(
           self,
           session_repo,
           class_repo,
           user_repo,
           connection_manager: ConnectionManager,
   ):
      self.session_repo = session_repo
      self.class_repo = class_repo
      self.user_repo = user_repo
      self.connection_manager = connection_manager

   async def execute(
           self, request: StartWaitingPhaseRequest, user_id: str
   ) -> StartWaitingPhaseResponse:
      # 1. Validate user permissions
      user = await self.user_repo.get_by_id(user_id)
      if not user:
         raise UserNotFoundError(user_id)

      # 2. Get session
      session = await self.session_repo.get_by_id(request.session_id)
      if not session:
         raise SessionNotFoundError(request.session_id)

      # 3. Verify teacher access if not admin
      if user.role == UserRole.TEACHER:
         await self._validate_teacher_access(user_id, session.class_id)
      elif user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
         raise NoPermissionToManageSessionError(user_id, request.session_id)

      # 4. Execute domain method
      session.start_waiting_phase()

      # 5. Persist changes
      updated_session = await self.session_repo.update(session)

      # 6. Broadcast to WebSocket clients
      await self.connection_manager.broadcast_to_session(
         request.session_id,
         WaitingRoomOpenedMessage(
            type="waiting_room_opened",
            session_id=request.session_id,
            timestamp=datetime.now(timezone.utc),
         ).dict(),
      )

      # 7. Return response DTO
      return StartWaitingPhaseResponse(
         id=updated_session.id,
         class_id=updated_session.class_id,
         test_id=updated_session.test_id,
         title=updated_session.title,
         scheduled_at=updated_session.scheduled_at,
         started_at=updated_session.started_at,
         completed_at=updated_session.completed_at,
         status=updated_session.status,
         participants=[
            ParticipantDTO(
               student_id=p.student_id,
               attempt_id=p.attempt_id,
               joined_at=p.joined_at,
               connection_status=p.connection_status,
               last_activity=p.last_activity,
            )
            for p in updated_session.participants
         ],
         created_by=updated_session.created_by,
         created_at=updated_session.created_at,
         updated_at=updated_session.updated_at,
      )

   async def _validate_teacher_access(self, teacher_id: str, class_id: str):
      """Validate that teacher teaches this class"""
      class_entity = await self.class_repo.get_by_id(class_id)
      if not class_entity:
         raise ClassNotFoundError(class_id)
      if teacher_id not in class_entity.teacher_ids:
         raise NoPermissionToManageSessionError(teacher_id, "session")
```

#### 3.2 Start Session Use Case

**Directory**: `/app/application/use_cases/sessions/commands/start_session/`

**Files**: Similar structure to Start Waiting, but:
- Calls `session.start_session()` which returns connected student IDs
- Broadcasts `SessionStartedMessage` with `started_at` and `connected_students`
- Response includes connected student count

#### 3.3 Complete Session Use Case

**Directory**: `/app/application/use_cases/sessions/commands/complete_session/`

**Files**: Similar structure, but:
- Calls `session.complete_session()`
- Broadcasts `SessionCompletedMessage`

#### 3.4 Delete Session Use Case

**Directory**: `/app/application/use_cases/sessions/commands/delete_session/`

**File**: `delete_session_use_case.py`

```python
from app.application.use_cases.authenticated_use_case import AuthenticatedUseCase
from app.domain.aggregates.users.user import UserRole
from app.domain.aggregates.session.session_status import SessionStatus
from app.domain.errors.session_errors import (
   SessionNotFoundError,
   CannotDeleteSessionError,
)
from app.domain.errors.common_errors import ForbiddenError
from .delete_session_dto import DeleteSessionRequest, DeleteSessionResponse


class DeleteSessionUseCase(
   AuthenticatedUseCase[DeleteSessionRequest, DeleteSessionResponse]
):
   def __init__(self, session_repo, user_repo, connection_manager):
      self.session_repo = session_repo
      self.user_repo = user_repo
      self.connection_manager = connection_manager

   async def execute(
           self, request: DeleteSessionRequest, user_id: str
   ) -> DeleteSessionResponse:
      # 1. Validate user is ADMIN
      user = await self.user_repo.get_by_id(user_id)
      if not user or user.role != UserRole.ADMIN:
         raise ForbiddenError("Only admins can delete sessions")

      # 2. Get session
      session = await self.session_repo.get_by_id(request.session_id)
      if not session:
         raise SessionNotFoundError(request.session_id)

      # 3. Validate session is not IN_PROGRESS
      if session.status == SessionStatus.IN_PROGRESS:
         raise CannotDeleteSessionError(request.session_id)

      # 4. Delete from repository
      await self.session_repo.delete(request.session_id)

      # 5. Return success
      return DeleteSessionResponse(success=True)
```

#### 3.5 Join Session Use Case

**Directory**: `/app/application/use_cases/sessions/commands/join_session/`

**Purpose**: Called when student WebSocket connects

**Logic**:
1. Validate student is participant in session
2. Call `session.student_join(student_id)`
3. Persist
4. Broadcast `ParticipantJoinedMessage` with connected count

#### 3.6 Disconnect Session Use Case

**Directory**: `/app/application/use_cases/sessions/commands/disconnect_session/`

**Purpose**: Called when student WebSocket disconnects

**Logic**:
1. Get session
2. Call `session.student_disconnect(student_id)`
3. Persist
4. Broadcast `ParticipantDisconnectedMessage`

---

### Step 4: Presentation Layer - Routes

#### 4.1 Add REST Endpoints

**File**: `/app/presentation/routes/session_router.py`

Add these endpoints to the existing router:

```python
from fastapi import APIRouter, Depends, status
from app.presentation.security.dependencies import RequireRoles
from app.domain.aggregates.users.user import UserRole

@router.post(
    "/{session_id}/start-waiting",
    response_model=StartWaitingPhaseResponse,
    summary="Open Waiting Room",
    description="Transition session to WAITING_FOR_STUDENTS status. "
                "Students can join once waiting room is open.",
)
async def start_waiting_room(
    session_id: str,
    current_user=Depends(RequireRoles([UserRole.ADMIN, UserRole.TEACHER])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    request = StartWaitingPhaseRequest(session_id=session_id)
    return await use_cases.start_waiting_use_case.execute(
        request, user_id=current_user["user_id"]
    )

@router.post(
    "/{session_id}/start",
    response_model=StartSessionResponse,
    summary="Start Session Countdown",
    description="Start the session and begin countdown for all connected students.",
)
async def start_session(
    session_id: str,
    current_user=Depends(RequireRoles([UserRole.ADMIN, UserRole.TEACHER])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    request = StartSessionRequest(session_id=session_id)
    return await use_cases.start_session_use_case.execute(
        request, user_id=current_user["user_id"]
    )

@router.post(
    "/{session_id}/complete",
    response_model=CompleteSessionResponse,
    summary="Complete Session",
    description="Force complete the session. Useful for ending early.",
)
async def complete_session(
    session_id: str,
    current_user=Depends(RequireRoles([UserRole.ADMIN, UserRole.TEACHER])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    request = CompleteSessionRequest(session_id=session_id)
    return await use_cases.complete_session_use_case.execute(
        request, user_id=current_user["user_id"]
    )

@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session",
    description="Delete a session. Admin only. Cannot delete IN_PROGRESS sessions.",
)
async def delete_session(
    session_id: str,
    current_user=Depends(RequireRoles([UserRole.ADMIN])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    request = DeleteSessionRequest(session_id=session_id)
    await use_cases.delete_session_use_case.execute(
        request, user_id=current_user["user_id"]
    )
    return None
```

#### 4.2 Create WebSocket Router

**File**: `/app/presentation/routes/websocket_router.py`

```python
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.web_socket import ConnectionManager, ConnectedMessage, ErrorMessage
from app.infrastructure.web_socket.websocket_auth import validate_websocket_access
from app.domain.aggregates.users.user import UserRole
from app.common.dependencies import (
   get_jwt_service,
   get_connection_manager,
   get_session_use_cases,
   get_class_use_cases,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["WebSocket"])


@router.websocket("/{session_id}/ws")
async def session_websocket_endpoint(
        websocket: WebSocket,
        session_id: str,
        token: str = Query(...),
        jwt_service: JwtService = Depends(get_jwt_service),
        manager: ConnectionManager = Depends(get_connection_manager),
        session_use_cases=Depends(get_session_use_cases),
        class_use_cases=Depends(get_class_use_cases),
):
   # 1. Validate token before accepting
   try:
      payload = jwt_service.decode(token)
      user_id = payload["user_id"]
      role = UserRole(payload["role"])
   except Exception as e:
      logger.error(f"WebSocket auth failed: {e}")
      await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
      return

   # 2. Get session and validate access
   try:
      session = await session_use_cases.get_session_by_id_use_case.execute(
         GetSessionByIdRequest(session_id=session_id)
      )

      has_access = await validate_websocket_access(
         user_id=user_id,
         role=role,
         session=session,
         class_repo=class_use_cases.class_repository,
      )

      if not has_access:
         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
         return
   except Exception as e:
      logger.error(f"Session validation failed: {e}")
      await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
      return

   # 3. Accept connection
   await websocket.accept()
   await manager.connect(session_id, user_id, websocket)

   # 4. Auto-join if student
   if role == UserRole.STUDENT:
      try:
         await session_use_cases.join_session_use_case.execute(
            JoinSessionRequest(session_id=session_id),
            user_id=user_id,
         )
      except Exception as e:
         logger.error(f"Auto-join failed: {e}")

   # 5. Send confirmation
   await websocket.send_json(
      ConnectedMessage(
         type="connected",
         session_id=session_id,
         timestamp=datetime.now(timezone.utc),
      ).dict()
   )

   try:
      # 6. Message loop
      while True:
         data = await websocket.receive_json()
         # Handle heartbeat, etc.
         if data.get("type") == "heartbeat":
            await websocket.send_json({"type": "pong"})
   except WebSocketDisconnect:
      logger.info(f"WebSocket disconnected: {user_id}")
   except Exception as e:
      logger.error(f"WebSocket error: {e}")
   finally:
      # 7. Cleanup
      await manager.disconnect(session_id, user_id)
      if role == UserRole.STUDENT:
         try:
            await session_use_cases.disconnect_session_use_case.execute(
               DisconnectSessionRequest(session_id=session_id),
               user_id=user_id,
            )
         except Exception as e:
            logger.error(f"Disconnect cleanup failed: {e}")
```

---

### Step 5: Dependency Injection

#### 5.1 Update Container

**File**: `/app/container.py`

Add providers:

```python
from app.infrastructure.web_socket import ConnectionManager


class ApplicationContainer(containers.DeclarativeContainer):
   # ... existing providers ...

   # WebSocket
   connection_manager = providers.Singleton(ConnectionManager)

   # New use cases (Factory pattern)
   start_waiting_use_case = providers.Factory(
      StartWaitingUseCase,
      session_repo=session_repository,
      class_repo=class_repository,
      user_repo=user_repository,
      connection_manager=connection_manager,
   )

   start_session_use_case = providers.Factory(
      StartSessionUseCase,
      session_repo=session_repository,
      class_repo=class_repository,
      user_repo=user_repository,
      connection_manager=connection_manager,
   )

   complete_session_use_case = providers.Factory(
      CompleteSessionUseCase,
      session_repo=session_repository,
      class_repo=class_repository,
      user_repo=user_repository,
      connection_manager=connection_manager,
   )

   delete_session_use_case = providers.Factory(
      DeleteSessionUseCase,
      session_repo=session_repository,
      user_repo=user_repository,
      connection_manager=connection_manager,
   )

   join_session_use_case = providers.Factory(
      JoinSessionUseCase,
      session_repo=session_repository,
      connection_manager=connection_manager,
   )

   disconnect_session_use_case = providers.Factory(
      DisconnectSessionUseCase,
      session_repo=session_repository,
      connection_manager=connection_manager,
   )
```

#### 5.2 Update Dependencies

**File**: `/app/common/dependencies.py`

Update `SessionUseCases` dataclass:

```python
from dataclasses import dataclass

@dataclass
class SessionUseCases:
    # Existing
    create_session_use_case: CreateSessionUseCase
    list_sessions_use_case: ListSessionsUseCase
    get_session_by_id_use_case: GetSessionByIdUseCase
    get_my_sessions_use_case: GetMySessionsUseCase

    # New
    start_waiting_use_case: StartWaitingUseCase
    start_session_use_case: StartSessionUseCase
    complete_session_use_case: CompleteSessionUseCase
    delete_session_use_case: DeleteSessionUseCase
    join_session_use_case: JoinSessionUseCase
    disconnect_session_use_case: DisconnectSessionUseCase

def get_connection_manager() -> ConnectionManager:
    """Get ConnectionManager singleton"""
    return container.connection_manager()
```

#### 5.3 Register WebSocket Router

**File**: `/app/main.py`

```python
from app.presentation.routes import websocket_router

app.include_router(websocket_router.router, prefix="/api/v1")
```

---

## Testing Guide

### Manual Testing Flow

1. **Create session** (existing):
   ```bash
   POST /api/v1/sessions
   # Returns session_id in SCHEDULED status
   ```

2. **Connect WebSocket as student**:
   ```javascript
   ws = new WebSocket(`ws://localhost:8000/api/v1/sessions/{session_id}/ws?token={jwt}`)
   // Should receive: {"type": "connected"}
   ```

3. **Start waiting room**:
   ```bash
   POST /api/v1/sessions/{session_id}/start-waiting
   # All WebSocket clients receive: {"type": "waiting_room_opened"}
   ```

4. **Start session**:
   ```bash
   POST /api/v1/sessions/{session_id}/start
   # All clients receive: {"type": "session_started", "started_at": "..."}
   ```

5. **Complete session**:
   ```bash
   POST /api/v1/sessions/{session_id}/complete
   # All clients receive: {"type": "session_completed"}
   ```

6. **Delete session**:
   ```bash
   DELETE /api/v1/sessions/{session_id}
   # Should return 204 No Content (only if not IN_PROGRESS)
   ```

---

## Performance Benefits

**Polling (REST only)**:
- 30 students × 1 request every 2 seconds = 900 requests/minute per session
- High database load
- 2-second delay in updates

**WebSocket**:
- 30 persistent connections
- 0 polling requests
- Instant updates on state changes
- Significantly lower server load

---

## Summary

This addendum provides the complete implementation details for:
- ✅ 4 new REST endpoints for session management
- ✅ WebSocket infrastructure for real-time updates
- ✅ 6 new use cases with proper permissions
- ✅ Message protocol for WebSocket communication
- ✅ ConnectionManager for WebSocket lifecycle
- ✅ Auto-join/disconnect handling
- ✅ Authentication and authorization
- ✅ Backward compatibility (REST works without WebSocket)

The WebSocket implementation follows the hybrid approach where use cases directly call the ConnectionManager after successful domain operations, ensuring that broadcasts only happen when data is successfully persisted.
