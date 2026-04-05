from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, model_validator
from utils.enums import EmploymentStatusEnum as employmentStatusEnum
from schemas.addressSchema import WorkAddressCreate


class ProfessionCreate(BaseModel):
    employment_status: employmentStatusEnum
    job_title: Optional[str] = None
    organization_name: Optional[str] = None
    annual_income: Optional[int] = None
    start_year: Optional[int] = None
    description: Optional[str] = None
    work_address : Optional[WorkAddressCreate] = None
    
    @model_validator(mode="after")
    def validate_profession(self):
        
        status = self.employment_status
        
        current_year = datetime.now().year
        
        if status == employmentStatusEnum.freelancer:
            if not self.job_title:
                raise ValueError("job_title is required for freelancer status")
            if self.annual_income is None:
                raise ValueError("annual_income is required for freelancer status")
            if self.start_year is None:
                raise ValueError("start_year is required for freelancer status")
            if self.start_year > current_year:
                raise ValueError("start_year cannot be in the future")
            
        if status in {
            employmentStatusEnum.employed,
            employmentStatusEnum.government_job,
        }:
            if not self.job_title:
                raise ValueError("job_title is required for employed and government_job statuses")
            if not self.organization_name:
                raise ValueError("organization_name is required for employed and government_job statuses")
            if self.annual_income is None:
                raise ValueError("annual_income is required for employed and government_job statuses")
            if self.start_year is None:
                raise ValueError("start_year is required for employed and government_job statuses")
            if self.start_year > current_year:
                raise ValueError("start_year cannot be in the future")
            if self.work_address is None:
                raise ValueError("work_address is required for employed and government_job statuses")
        
    
        if status == employmentStatusEnum.business_owner:
            if not self.job_title:
                raise ValueError("job_title is required for business_owner status")
            if not self.organization_name:
                raise ValueError("organization_name is required for business_owner status")
            if self.annual_income is None:
                raise ValueError("annual_income is required for business_owner status")
            if self.start_year is None:
                raise ValueError("start_year is required for business_owner status")
            if self.start_year > current_year:
                raise ValueError("start_year cannot be in the future")
            if self.description is None:
                raise ValueError("description is required for business_owner status")
            if self.work_address is None:
                raise ValueError("work_address is required for business_owner status")
            
        if status in {
            employmentStatusEnum.unemployed,
            employmentStatusEnum.student,
        }:
            if self.job_title is not None:
                raise ValueError("job_title should not be provided for unemployed, student statuses")
            if self.organization_name is not None:
                raise ValueError("organization_name should not be provided for unemployed, student statuses")
            if self.annual_income is not None:
                raise ValueError("annual_income should not be provided for unemployed, student statuses")
            if self.start_year is not None:
                raise ValueError("start_year should not be provided for unemployed, student statuses")
            if self.description is not None:
                raise ValueError("description should not be provided for unemployed, student statuses")
    
    
        if status == employmentStatusEnum.retired:
            if self.job_title is not None:
                raise ValueError("job_title should not be provided for retired status")
            if self.organization_name is not None:
                raise ValueError("organization_name should not be provided for retired status")
            if self.start_year is not None:
                raise ValueError("start_year should not be provided for retired status")
            if self.work_address is not None:
                raise ValueError("work_address should not be provided for retired status")
        
        return self
    
class professionResponse(BaseModel):
    id: str
    employment_status: employmentStatusEnum
    job_title: Optional[str] = None
    organization_name: Optional[str] = None
    annual_income: Optional[int] = None
    start_year: Optional[int] = None
    description: Optional[str] = None