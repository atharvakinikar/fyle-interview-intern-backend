from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment
from .schema import AssignmentSchema, AssignmentGradeSchema
principal_assignments_resources = Blueprint('principal_assignments_resources', __name__)

@principal_assignments_resources.route('/assignments',methods=['GET'],strict_slashes=False)
@decorators.authenticate_principal
def list_graded_submitted_assignments(p):
    """Returns list of submitted and graded assignments"""

    # Fetching the assignments whose state are GRADED or SUBMITTED
    graded_submitted_assignments = Assignment.get_assignments_graded_submitted()

    # Serializing the assignments which are either GRADED or SUBMITTED
    graded_submitted_assignments_dump = AssignmentSchema().dump(graded_submitted_assignments, many=True)

    return APIResponse.respond(data=graded_submitted_assignments_dump)

@principal_assignments_resources.route('/assignments/grade',methods=['POST'],strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def grade_or_regrade_assignment(p,incoming_payload):
    """Grades or regrades the assignment"""

    # Deserializing the data received from payload
    grade_assignment_payload = AssignmentGradeSchema().load(incoming_payload)

    # Marking the grade and updating in database by calling the mark_grade function
    graded_assignment = Assignment.mark_grade(
        _id=grade_assignment_payload.id,
        grade=grade_assignment_payload.grade,
        auth_principal=p
    )
    db.session.commit()
    graded_assignment_dump = AssignmentSchema().dump(graded_assignment)
    return APIResponse.respond(data=graded_assignment_dump)