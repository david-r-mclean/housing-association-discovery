"""
Industry Configuration System
Defines search parameters and data sources for different industries
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class IndustryType(Enum):
    HOUSING_ASSOCIATIONS = "housing_associations"
    CHARITIES = "charities"
    CARE_HOMES = "care_homes"
    SCHOOLS = "schools"
    HEALTHCARE = "healthcare"
    SOCIAL_ENTERPRISES = "social_enterprises"
    COOPERATIVES = "cooperatives"
    CREDIT_UNIONS = "credit_unions"
    COMMUNITY_GROUPS = "community_groups"
    ENVIRONMENTAL_ORGS = "environmental_orgs"

@dataclass
class DataSource:
    name: str
    url: str
    type: str  # 'regulator', 'directory', 'api', 'scrape'
    search_params: Dict
    data_fields: List[str]
    rate_limit: float = 1.0  # seconds between requests

@dataclass
class IndustryConfig:
    name: str
    description: str
    industry_type: IndustryType
    data_sources: List[DataSource]
    search_keywords: List[str]
    company_types: List[str]
    sic_codes: List[str]  # Standard Industrial Classification codes
    website_indicators: List[str]  # What to look for on websites
    ai_analysis_prompts: Dict[str, str]
    output_fields: List[str]

class IndustryConfigManager:
    """Manages industry configurations and search parameters"""
    
    def __init__(self):
        self.configs = self._load_default_configs()
    
    def _load_default_configs(self) -> Dict[IndustryType, IndustryConfig]:
        """Load default industry configurations"""
        return {
            IndustryType.HOUSING_ASSOCIATIONS: self._housing_associations_config(),
            IndustryType.CHARITIES: self._charities_config(),
            IndustryType.CARE_HOMES: self._care_homes_config(),
            IndustryType.SCHOOLS: self._schools_config(),
            IndustryType.HEALTHCARE: self._healthcare_config(),
            IndustryType.SOCIAL_ENTERPRISES: self._social_enterprises_config(),
            IndustryType.COOPERATIVES: self._cooperatives_config(),
            IndustryType.CREDIT_UNIONS: self._credit_unions_config(),
            IndustryType.COMMUNITY_GROUPS: self._community_groups_config(),
            IndustryType.ENVIRONMENTAL_ORGS: self._environmental_orgs_config()
        }
    
    def _housing_associations_config(self) -> IndustryConfig:
        """Housing Associations configuration"""
        return IndustryConfig(
            name="Housing Associations",
            description="Social housing providers and registered social landlords",
            industry_type=IndustryType.HOUSING_ASSOCIATIONS,
            data_sources=[
                DataSource(
                    name="Scottish Housing Regulator",
                    url="https://www.housingregulator.gov.scot",
                    type="regulator",
                    search_params={"region": "scotland", "type": "rsl"},
                    data_fields=["name", "registration_number", "stock_units", "satisfaction_score"],
                    rate_limit=2.0
                ),
                DataSource(
                    name="Regulator of Social Housing (England)",
                    url="https://www.gov.uk/government/organisations/regulator-of-social-housing",
                    type="regulator",
                    search_params={"region": "england", "type": "rp"},
                    data_fields=["name", "registration_number", "stock_units", "governance_rating"],
                    rate_limit=2.0
                ),
                DataSource(
                    name="Companies House",
                    url="https://find-and-update.company-information.service.gov.uk",
                    type="api",
                    search_params={"sic_codes": ["91110", "68100", "68209"]},
                    data_fields=["company_number", "company_name", "company_status", "incorporation_date"],
                    rate_limit=0.6
                )
            ],
            search_keywords=["housing association", "social housing", "registered social landlord", "RSL", "housing society"],
            company_types=["Community Interest Company", "Industrial and Provident Society", "Company Limited by Guarantee"],
            sic_codes=["91110", "68100", "68209", "68320"],
            website_indicators=["tenant portal", "housing application", "rent payment", "repairs", "maintenance"],
            ai_analysis_prompts={
                "digital_maturity": "Analyze the digital capabilities of this housing association, focusing on tenant services, online applications, and digital transformation.",
                "service_quality": "Assess the service quality indicators including tenant satisfaction, complaints handling, and service delivery.",
                "transformation_opportunities": "Identify opportunities for digital transformation and service improvement in social housing."
            },
            output_fields=["name", "registration_number", "stock_units", "digital_maturity_score", "tenant_portal", "satisfaction_score"]
        )
    
    def _charities_config(self) -> IndustryConfig:
        """Charities configuration"""
        return IndustryConfig(
            name="Charities",
            description="Registered charities and non-profit organizations",
            industry_type=IndustryType.CHARITIES,
            data_sources=[
                DataSource(
                    name="Charity Commission for England and Wales",
                    url="https://register-of-charities.charitycommission.gov.uk",
                    type="api",
                    search_params={"region": "england_wales"},
                    data_fields=["charity_number", "charity_name", "income", "activities"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Office of the Scottish Charity Regulator (OSCR)",
                    url="https://www.oscr.org.uk",
                    type="api",
                    search_params={"region": "scotland"},
                    data_fields=["charity_number", "charity_name", "income", "purposes"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Charity Commission for Northern Ireland",
                    url="https://www.charitycommissionni.org.uk",
                    type="api",
                    search_params={"region": "northern_ireland"},
                    data_fields=["charity_number", "charity_name", "income", "activities"],
                    rate_limit=1.0
                )
            ],
            search_keywords=["charity", "non-profit", "voluntary", "community", "foundation", "trust"],
            company_types=["Charitable Incorporated Organisation", "Company Limited by Guarantee", "Unincorporated Association"],
            sic_codes=["94910", "94920", "94990", "88910", "88990"],
            website_indicators=["donate", "volunteer", "fundraising", "impact", "mission", "causes"],
            ai_analysis_prompts={
                "impact_assessment": "Analyze the social impact and effectiveness of this charity's work.",
                "digital_fundraising": "Assess the charity's digital fundraising capabilities and online presence.",
                "transparency": "Evaluate the transparency and accountability of this charity's operations."
            },
            output_fields=["charity_name", "charity_number", "income", "digital_fundraising_score", "transparency_score", "impact_areas"]
        )
    
    def _care_homes_config(self) -> IndustryConfig:
        """Care Homes configuration"""
        return IndustryConfig(
            name="Care Homes",
            description="Residential care facilities and nursing homes",
            industry_type=IndustryType.CARE_HOMES,
            data_sources=[
                DataSource(
                    name="Care Quality Commission (CQC)",
                    url="https://www.cqc.org.uk",
                    type="regulator",
                    search_params={"service_type": "residential_care"},
                    data_fields=["provider_name", "location_name", "overall_rating", "inspection_date"],
                    rate_limit=2.0
                ),
                DataSource(
                    name="Care Inspectorate Scotland",
                    url="https://www.careinspectorate.com",
                    type="regulator",
                    search_params={"service_type": "care_home"},
                    data_fields=["service_name", "provider_name", "grades", "inspection_date"],
                    rate_limit=2.0
                )
            ],
            search_keywords=["care home", "nursing home", "residential care", "elderly care", "dementia care"],
            company_types=["Private Limited Company", "Partnership", "Sole Proprietorship"],
            sic_codes=["87100", "87200", "87300", "87900"],
            website_indicators=["care services", "residents", "families", "visiting", "fees", "admissions"],
            ai_analysis_prompts={
                "care_quality": "Analyze the quality of care provided by this facility based on inspection reports and ratings.",
                "digital_services": "Assess the digital services offered to residents and families.",
                "compliance": "Evaluate regulatory compliance and safety standards."
            },
            output_fields=["provider_name", "location_name", "overall_rating", "care_quality_score", "digital_services", "bed_capacity"]
        )
    
    def _schools_config(self) -> IndustryConfig:
        """Schools configuration"""
        return IndustryConfig(
            name="Schools",
            description="Educational institutions including primary, secondary, and special schools",
            industry_type=IndustryType.SCHOOLS,
            data_sources=[
                DataSource(
                    name="Get Information About Schools (GIAS)",
                    url="https://get-information-schools.service.gov.uk",
                    type="api",
                    search_params={"region": "england"},
                    data_fields=["school_name", "urn", "phase", "ofsted_rating"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Scottish Government School Information",
                    url="https://www.gov.scot/policies/schools/",
                    type="api",
                    search_params={"region": "scotland"},
                    data_fields=["school_name", "local_authority", "school_type", "roll"],
                    rate_limit=1.0
                )
            ],
            search_keywords=["school", "academy", "college", "education", "primary", "secondary"],
            company_types=["Academy Trust", "Foundation School", "Community School"],
            sic_codes=["85100", "85200", "85310", "85320"],
            website_indicators=["pupils", "students", "curriculum", "admissions", "parents", "learning"],
            ai_analysis_prompts={
                "educational_quality": "Analyze the educational quality and performance of this school.",
                "digital_learning": "Assess the school's digital learning capabilities and technology integration.",
                "community_engagement": "Evaluate the school's engagement with parents and the local community."
            },
            output_fields=["school_name", "urn", "ofsted_rating", "digital_learning_score", "pupil_count", "performance_indicators"]
        )
    
    def _healthcare_config(self) -> IndustryConfig:
        """Healthcare configuration"""
        return IndustryConfig(
            name="Healthcare Providers",
            description="NHS trusts, private healthcare providers, and medical practices",
            industry_type=IndustryType.HEALTHCARE,
            data_sources=[
                DataSource(
                    name="NHS Digital",
                    url="https://digital.nhs.uk",
                    type="api",
                    search_params={"service_type": "healthcare"},
                    data_fields=["organisation_name", "organisation_code", "services", "location"],
                    rate_limit=2.0
                ),
                DataSource(
                    name="Care Quality Commission",
                    url="https://www.cqc.org.uk",
                    type="regulator",
                    search_params={"service_type": "healthcare"},
                    data_fields=["provider_name", "location_name", "overall_rating", "services"],
                    rate_limit=2.0
                )
            ],
            search_keywords=["NHS", "hospital", "clinic", "medical practice", "healthcare", "GP surgery"],
            company_types=["NHS Foundation Trust", "NHS Trust", "Private Limited Company"],
            sic_codes=["86100", "86210", "86220", "86230"],
            website_indicators=["appointments", "patients", "medical services", "consultations", "treatments"],
            ai_analysis_prompts={
                "service_quality": "Analyze the quality of healthcare services provided by this organization.",
                "digital_health": "Assess the digital health services and patient portal capabilities.",
                "patient_experience": "Evaluate patient experience and satisfaction indicators."
            },
            output_fields=["organisation_name", "organisation_code", "overall_rating", "digital_health_score", "patient_services", "specialties"]
        )
    
    def _social_enterprises_config(self) -> IndustryConfig:
        """Social Enterprises configuration"""
        return IndustryConfig(
            name="Social Enterprises",
            description="Businesses with social or environmental missions",
            industry_type=IndustryType.SOCIAL_ENTERPRISES,
            data_sources=[
                DataSource(
                    name="Social Enterprise Directory",
                    url="https://www.socialenterprisedirectory.org.uk",
                    type="directory",
                    search_params={"type": "social_enterprise"},
                    data_fields=["name", "location", "sector", "social_impact"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Companies House CIC Register",
                    url="https://find-and-update.company-information.service.gov.uk",
                    type="api",
                    search_params={"company_type": "community_interest_company"},
                    data_fields=["company_number", "company_name", "company_status", "sic_codes"],
                    rate_limit=0.6
                )
            ],
            search_keywords=["social enterprise", "community interest company", "CIC", "social business", "impact"],
            company_types=["Community Interest Company", "Company Limited by Guarantee", "Industrial and Provident Society"],
            sic_codes=["94990", "88990", "91040", "94920"],
            website_indicators=["social impact", "community", "sustainability", "mission", "values", "change"],
            ai_analysis_prompts={
                "social_impact": "Analyze the social impact and mission effectiveness of this social enterprise.",
                "sustainability": "Assess the environmental and social sustainability practices.",
                "business_model": "Evaluate the business model and financial sustainability."
            },
            output_fields=["name", "company_number", "social_impact_score", "sustainability_score", "sector", "mission_areas"]
        )
    
    def _cooperatives_config(self) -> IndustryConfig:
        """Cooperatives configuration"""
        return IndustryConfig(
            name="Cooperatives",
            description="Member-owned cooperative businesses and societies",
            industry_type=IndustryType.COOPERATIVES,
            data_sources=[
                DataSource(
                    name="Cooperatives UK Directory",
                    url="https://www.uk.coop",
                    type="directory",
                    search_params={"type": "cooperative"},
                    data_fields=["name", "location", "sector", "membership"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Financial Conduct Authority Mutuals Register",
                    url="https://www.fca.org.uk",
                    type="regulator",
                    search_params={"type": "mutual"},
                    data_fields=["society_name", "registration_number", "business_type"],
                    rate_limit=2.0
                )
            ],
            search_keywords=["cooperative", "co-op", "mutual", "society", "member-owned"],
            company_types=["Industrial and Provident Society", "Community Benefit Society", "Cooperative Society"],
            sic_codes=["64191", "64209", "47110", "01610"],
            website_indicators=["members", "cooperative", "community owned", "democratic", "values"],
            ai_analysis_prompts={
                "cooperative_principles": "Analyze how well this cooperative adheres to cooperative principles and values.",
                "member_engagement": "Assess member engagement and democratic participation.",
                "community_impact": "Evaluate the cooperative's impact on the local community."
            },
            output_fields=["name", "registration_number", "cooperative_principles_score", "member_count", "sector", "community_impact"]
        )
    
    def _credit_unions_config(self) -> IndustryConfig:
        """Credit Unions configuration"""
        return IndustryConfig(
            name="Credit Unions",
            description="Member-owned financial cooperatives",
            industry_type=IndustryType.CREDIT_UNIONS,
            data_sources=[
                DataSource(
                    name="Association of British Credit Unions Limited (ABCUL)",
                    url="https://www.abcul.org",
                    type="directory",
                    search_params={"type": "credit_union"},
                    data_fields=["name", "location", "membership", "assets"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Financial Conduct Authority",
                    url="https://www.fca.org.uk",
                    type="regulator",
                    search_params={"type": "credit_union"},
                    data_fields=["name", "registration_number", "status"],
                    rate_limit=2.0
                )
            ],
            search_keywords=["credit union", "financial cooperative", "community banking", "savings", "loans"],
            company_types=["Industrial and Provident Society", "Credit Union"],
            sic_codes=["64191", "64920", "64929"],
            website_indicators=["savings", "loans", "members", "financial services", "community"],
            ai_analysis_prompts={
                "financial_health": "Analyze the financial health and stability of this credit union.",
                "member_services": "Assess the range and quality of services offered to members.",
                "digital_banking": "Evaluate digital banking capabilities and online services."
            },
            output_fields=["name", "registration_number", "financial_health_score", "member_count", "digital_services", "asset_size"]
        )
    
    def _community_groups_config(self) -> IndustryConfig:
        """Community Groups configuration"""
        return IndustryConfig(
            name="Community Groups",
            description="Local community organizations and voluntary groups",
            industry_type=IndustryType.COMMUNITY_GROUPS,
            data_sources=[
                DataSource(
                    name="Community Groups Directory",
                    url="https://www.communitygroups.org.uk",
                    type="directory",
                    search_params={"type": "community_group"},
                    data_fields=["name", "location", "activities", "volunteers"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Local Authority Directories",
                    url="various",
                    type="directory",
                    search_params={"type": "voluntary_sector"},
                    data_fields=["name", "contact", "services", "area"],
                    rate_limit=1.0
                )
            ],
            search_keywords=["community group", "voluntary group", "residents association", "community centre"],
            company_types=["Unincorporated Association", "Company Limited by Guarantee", "Charitable Incorporated Organisation"],
            sic_codes=["94990", "94920", "91040", "93110"],
            website_indicators=["community", "volunteers", "local", "events", "activities", "residents"],
            ai_analysis_prompts={
                "community_impact": "Analyze the impact this group has on the local community.",
                "volunteer_engagement": "Assess volunteer engagement and community participation.",
                "sustainability": "Evaluate the long-term sustainability of the organization."
            },
            output_fields=["name", "location", "community_impact_score", "volunteer_count", "activities", "sustainability_score"]
        )
    
    def _environmental_orgs_config(self) -> IndustryConfig:
        """Environmental Organizations configuration"""
        return IndustryConfig(
            name="Environmental Organizations",
            description="Environmental charities, conservation groups, and green organizations",
            industry_type=IndustryType.ENVIRONMENTAL_ORGS,
            data_sources=[
                DataSource(
                    name="Environmental Charities Directory",
                    url="https://www.environmentalcharities.org.uk",
                    type="directory",
                    search_params={"type": "environmental"},
                    data_fields=["name", "location", "focus_areas", "projects"],
                    rate_limit=1.0
                ),
                DataSource(
                    name="Charity Commission",
                    url="https://register-of-charities.charitycommission.gov.uk",
                    type="api",
                    search_params={"classification": "environmental"},
                    data_fields=["charity_number", "charity_name", "income", "activities"],
                    rate_limit=1.0
                )
            ],
            search_keywords=["environmental", "conservation", "sustainability", "climate", "green", "ecology"],
            company_types=["Charitable Incorporated Organisation", "Company Limited by Guarantee", "Trust"],
            sic_codes=["94990", "91040", "84120", "39000"],
            website_indicators=["environment", "conservation", "sustainability", "climate change", "green", "carbon"],
            ai_analysis_prompts={
                "environmental_impact": "Analyze the environmental impact and effectiveness of this organization.",
                "sustainability_practices": "Assess the organization's own sustainability practices.",
                "climate_action": "Evaluate the organization's contribution to climate action and environmental protection."
            },
            output_fields=["name", "charity_number", "environmental_impact_score", "focus_areas", "sustainability_practices", "climate_action"]
        )
    
    def get_config(self, industry_type: IndustryType) -> IndustryConfig:
        """Get configuration for a specific industry"""
        return self.configs.get(industry_type)
    
    def get_all_configs(self) -> Dict[IndustryType, IndustryConfig]:
        """Get all industry configurations"""
        return self.configs
    
    def get_industry_names(self) -> List[str]:
        """Get list of all industry names"""
        return [config.name for config in self.configs.values()]
    
    def get_config_by_name(self, name: str) -> Optional[IndustryConfig]:
        """Get configuration by industry name"""
        for config in self.configs.values():
            if config.name.lower() == name.lower():
                return config
        return None