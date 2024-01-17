import enum
from core import db
from core.apis.decorators import AuthPrincipal
from core.libs import helpers, assertions
from core.models.teachers import Teacher
from core.models.students import Student
from sqlalchemy.types import Enum as BaseEnum


class GradeEnum(str, enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class AssignmentStateEnum(str, enum.Enum):
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    GRADED = 'GRADED'


class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, db.Sequence('assignments_id_seq'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(Student.id), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey(Teacher.id), nullable=True)
    content = db.Column(db.Text)
    grade = db.Column(BaseEnum(GradeEnum))
    state = db.Column(BaseEnum(AssignmentStateEnum), default=AssignmentStateEnum.DRAFT, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=helpers.get_utc_now, nullable=False)
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=helpers.get_utc_now, nullable=False, onupdate=helpers.get_utc_now)

    def __repr__(self):
        return '<Assignment %r>' % self.id

    @classmethod
    def filter(cls, *criterion):
        db_query = db.session.query(cls)
        return db_query.filter(*criterion)

    @classmethod
    def get_by_id(cls, _id):
        return cls.filter(cls.id == _id).first()

    @classmethod
    def upsert(cls, assignment_new: 'Assignment'):

        # The content of assignment cannot be None
        assertions.assert_valid(assignment_new.content is not None, "The assignemnt content cannot be null")

        if assignment_new.id is not None:
            assignment = Assignment.get_by_id(assignment_new.id)
            assertions.assert_found(assignment, 'No assignment with this id was found')
            assertions.assert_valid(assignment.state == AssignmentStateEnum.DRAFT,
                                    'only assignment in draft state can be edited')

            assignment.content = assignment_new.content
        else:
            assignment = assignment_new
            db.session.add(assignment_new)

        db.session.flush()
        return assignment

    @classmethod
    def submit(cls, _id, teacher_id, auth_principal: AuthPrincipal):
        assignment = Assignment.get_by_id(_id)
        assertions.assert_found(assignment, 'No assignment with this id was found')
        assertions.assert_valid(assignment.student_id == auth_principal.student_id, 'This assignment belongs to some other student')
        assertions.assert_valid(assignment.content is not None, 'assignment with empty content cannot be submitted')

        # Only draft assignment can be submitted to teacher
        # Checking if the state of assignment is in draft state else raise an error
        assertions.assert_valid(assignment.state == AssignmentStateEnum.DRAFT.value, 'only a draft assignment can be submitted')

        assignment.teacher_id = teacher_id

        # Changing the state of assignment from DRAFT to SUBMITTED
        assignment.state = AssignmentStateEnum.SUBMITTED

        db.session.flush()
        return assignment

    @classmethod
    def mark_grade(cls, _id, grade, auth_principal: AuthPrincipal):
        assignment = Assignment.get_by_id(_id)
        assertions.assert_found(assignment, 'No assignment with this id was found')
        assertions.assert_valid(grade is not None, 'assignment with empty grade cannot be graded')

        # Checking for validity of grade
        assertions.assert_valid(grade in GradeEnum, 'invalid grade')

        # If the hedaer has the field 'teacher_id', then we need to check that there is no cross grading done by the teacher
        if hasattr(auth_principal, 'teacher_id') and auth_principal.teacher_id is not None:
            assertions.assert_valid(assignment.teacher_id == auth_principal.teacher_id, 'cross grading of assignment is now allowed')

        # If the header has the field 'principal_id', then we need to check that assignment state is not DRAFT
        if hasattr(auth_principal, 'principal_id') and auth_principal.principal_id is not None:
            assertions.assert_valid(assignment.state is not AssignmentStateEnum.DRAFT, 'Draft assignment cannot be graded by principal')

        assignment.grade = grade
        assignment.state = AssignmentStateEnum.GRADED
        db.session.flush()

        return assignment

    @classmethod
    def get_assignments_by_student(cls, student_id):
        return cls.filter(cls.student_id == student_id).all()

    @classmethod
    def get_assignments_by_teacher(cls, teacher_id):
        return cls.filter(cls.teacher_id == teacher_id).all()

    # get_by_state fetches all the assignments of a particular STATE
    @classmethod
    def get_by_state(cls, state: AssignmentStateEnum):
        return cls.filter(cls.state == state).all()

    @classmethod
    def get_assignments_graded_submitted(cls):

        submitted_assignments = Assignment.get_by_state(AssignmentStateEnum.SUBMITTED)
        graded_assignments = Assignment.get_by_state(AssignmentStateEnum.GRADED)

        # returning the combined list of submitted + graded assignments
        return submitted_assignments+graded_assignments