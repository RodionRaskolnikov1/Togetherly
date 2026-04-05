from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from utils.enums import EducationLevelEnum, PassingStatusEnum


class EducationCreate(BaseModel):
    level : EducationLevelEnum
    status : PassingStatusEnum
    
    course_name: Optional[str] = Field(None, max_length=100)
    stream: Optional[str] = Field(None, max_length=100)
    institution_name: Optional[str] = Field(None, max_length=150)
    board_name: Optional[str] = Field(None, max_length=150)
    school_name: Optional[str] = Field(None, max_length=150)
    university_name: Optional[str] = Field(None, max_length=150)
    
    percentage_or_cgpa: Optional[float] = None
    passing_year: Optional[int] = None
    last_class_completed: Optional[int] = None

    @model_validator(mode="after")
    def validate_education(self):
        level = self.level
        status = self.status

        current_year = datetime.now().year
        
        if level == EducationLevelEnum.below_ssc:
            if self.last_class_completed is None:
                raise ValueError("last_class_completed is required for below_ssc")
            if not (1 <= self.last_class_completed <= 9):
                raise ValueError("last_class_completed must be between 1 and 9")
            if not self.school_name:
                raise ValueError("school_name is required for below_ssc")

            
        if level == EducationLevelEnum.ssc:
            if not self.board_name:
                raise ValueError("board_name is required for ssc")
            if not self.school_name:
                raise ValueError("school_name is required for ssc")
            
            
        if level == EducationLevelEnum.hsc:
            if not self.board_name:
                raise ValueError("board_name is required for hsc")
            if not self.school_name:
                raise ValueError("school_name is required for hsc")
            if not self.stream:
                raise ValueError("stream is required for hsc")
            
            
            
            
        if level in {
            EducationLevelEnum.graduate,
            EducationLevelEnum.masters,
            EducationLevelEnum.higher_studies,
        }:
            if not self.course_name:
                raise ValueError("course_name is required for higher education")
            if not self.institution_name:
                raise ValueError("institution_name is required for higher education")
            if self.stream is not None:
                raise ValueError("stream is not applicable for higher education")
            if self.board_name is not None:
                raise ValueError("board_name is not applicable for higher education")
            if self.school_name is not None:
                raise ValueError("school_name is not applicable for higher education") 
            if self.last_class_completed is not None:
                raise ValueError("last_class_completed is not applicable for higher education")
            
        if level == EducationLevelEnum.diploma:
            if not self.course_name:
                raise ValueError("course_name is required for diploma")
            if not self.institution_name:
                raise ValueError("institution_name is required for diploma")
            
        if level == EducationLevelEnum.other:
            if not self.course_name:
                raise ValueError("course_name is required for other education type")
            
        
            
        if status == PassingStatusEnum.completed:
            if self.passing_year is None:
                raise ValueError("passing_year is required if education is completed")
            if self.passing_year > current_year:
                raise ValueError("passing_year cannot be in the future")
            if self.percentage_or_cgpa is None:
                raise ValueError("percentage_or_cgpa is required if education is completed")
            
        if status == PassingStatusEnum.pursuing:
            if self.passing_year is not None:
                raise ValueError("passing_year should be null if education is pursuing")
            if self.percentage_or_cgpa is not None:
                raise ValueError("percentage_or_cgpa should be null if education is pursuing")

        if status == PassingStatusEnum.failed:
            if self.passing_year is not None:
                raise ValueError("passing_year should not exist if status is failed")
        
        return self
    
    
    