# models package
from app.models.user import User, PelamarProfile, PerusahaanProfile, KampusProfile
from app.models.job import JobCategory, JobPosting
from app.models.application import CVDocument, Application
from app.models.analysis import CVAnalysisResult


from .setting import SystemSetting

from .audit import AuditLog

from app.models.video_task import VideoAnalysisJob
