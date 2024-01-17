from core.apis import decorators
from core.apis.responses import APIResponse
from core.apis.teachers.schema import TeacherSchema
from core.apis.assignments.principal import principal_assignments_resources
from core.models.teachers import Teacher


@principal_assignments_resources.route('/teachers',methods=['GET'],strict_slashes=False)
@decorators.authenticate_principal
def list_teachers(p):
    """Returns the list of teachers"""

    # Fetching the list of all teachers
    teachers_list = Teacher.get_all_teachers()

    # Serializing teacher data
    teacher_list_dump = TeacherSchema().dump(teachers_list,many=True)

    return APIResponse.respond(data=teacher_list_dump)