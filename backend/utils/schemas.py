from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime


class UserRegistrationSchema(Schema):
    """Schema for user registration."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    first_name = fields.Str(validate=validate.Length(max=50))
    last_name = fields.Str(validate=validate.Length(max=50))


class UserLoginSchema(Schema):
    """Schema for user login."""
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class IncidentSchema(Schema):
    """Schema for incident."""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(max=200))
    description = fields.Str()
    severity = fields.Str(validate=validate.OneOf(['SEV1', 'SEV2', 'SEV3', 'SEV4']))
    status = fields.Str(validate=validate.OneOf(['Open', 'Investigating', 'Mitigated', 'Resolved', 'Closed']))
    incident_type = fields.Str(validate=validate.Length(max=100))
    source = fields.Str(validate=validate.Length(max=100))
    detected_at = fields.DateTime(dump_only=True)
    resolved_at = fields.DateTime(allow_none=True)
    user_id = fields.Int(dump_only=True)
    log_file_path = fields.Str(dump_only=True)
    log_file_type = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    event_count = fields.Int(dump_only=True)


class IncidentCreateSchema(Schema):
    """Schema for creating incident."""
    title = fields.Str(required=True, validate=validate.Length(max=200))
    description = fields.Str()
    severity = fields.Str(validate=validate.OneOf(['SEV1', 'SEV2', 'SEV3', 'SEV4']), load_default='SEV3')
    status = fields.Str(validate=validate.OneOf(['Open', 'Investigating', 'Mitigated', 'Resolved', 'Closed']), load_default='Open')
    incident_type = fields.Str(validate=validate.Length(max=100))
    source = fields.Str(validate=validate.Length(max=100))


class IncidentUpdateSchema(Schema):
    """Schema for updating incident."""
    title = fields.Str(validate=validate.Length(max=200))
    description = fields.Str()
    severity = fields.Str(validate=validate.OneOf(['SEV1', 'SEV2', 'SEV3', 'SEV4']))
    status = fields.Str(validate=validate.OneOf(['Open', 'Investigating', 'Mitigated', 'Resolved', 'Closed']))
    incident_type = fields.Str(validate=validate.Length(max=100))
    source = fields.Str(validate=validate.Length(max=100))


class ReportSchema(Schema):
    """Schema for report."""
    id = fields.Int(dump_only=True)
    incident_id = fields.Int(required=True)
    user_id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(max=200))
    executive_summary = fields.Str()
    incident_overview = fields.Str()
    timeline = fields.Str()
    root_cause_analysis = fields.Str()
    impact_assessment = fields.Str()
    systems_affected = fields.Str()
    resolution_steps = fields.Str()
    recommendations = fields.Str()
    preventive_actions = fields.Str()
    lessons_learned = fields.Str()
    ai_model_used = fields.Str(dump_only=True)
    confidence_score = fields.Float(dump_only=True)
    generation_time = fields.Float(dump_only=True)
    status = fields.Str(validate=validate.OneOf(['draft', 'final', 'archived']))
    version = fields.Int(dump_only=True)
    report_file_path = fields.Str(dump_only=True)
    report_format = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ReportCreateSchema(Schema):
    """Schema for creating report."""
    incident_id = fields.Int(required=True)
    title = fields.Str(required=True, validate=validate.Length(max=200))


class ReportUpdateSchema(Schema):
    """Schema for updating report."""
    title = fields.Str(validate=validate.Length(max=200))
    executive_summary = fields.Str()
    incident_overview = fields.Str()
    timeline = fields.Str()
    root_cause_analysis = fields.Str()
    impact_assessment = fields.Str()
    systems_affected = fields.Str()
    resolution_steps = fields.Str()
    recommendations = fields.Str()
    preventive_actions = fields.Str()
    lessons_learned = fields.Str()
    status = fields.Str(validate=validate.OneOf(['draft', 'final', 'archived']))


class ReportGenerateSchema(Schema):
    """Schema for generating report."""
    incident_id = fields.Int(required=True)
    title = fields.Str(required=True, validate=validate.Length(max=200))


# Initialize schemas
user_schema = UserRegistrationSchema()
users_schema = UserRegistrationSchema(many=True)
user_login_schema = UserLoginSchema()

incident_schema = IncidentSchema()
incidents_schema = IncidentSchema(many=True)
incident_create_schema = IncidentCreateSchema()
incident_update_schema = IncidentUpdateSchema()

report_schema = ReportSchema()
reports_schema = ReportSchema(many=True)
report_create_schema = ReportCreateSchema()
report_update_schema = ReportUpdateSchema()
report_generate_schema = ReportGenerateSchema()
