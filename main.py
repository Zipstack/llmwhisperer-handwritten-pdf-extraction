import sys
from dotenv import load_dotenv
from unstract.llmwhisperer.client import LLMWhispererClient, LLMWhispererClientException
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

class PersonalDetails(BaseModel):
    name: str = Field(description="Name of the individual")
    ssn: str = Field(description="Social Security Number of the individual")
    dob: datetime = Field(description="Date of birth of the individual")
    citizenship: str = Field(description="Citizenship of the individual")


class ExtraDetails(BaseModel):
    type_of_credit: str = Field(description="Type of credit")
    marital_status: str = Field(description="Marital status")
    cell_phone: str = Field(description="Cell phone number")


class CurrentAddress(BaseModel):
    street: str = Field(description="Street address")
    city: str = Field(description="City")
    state: str = Field(description="State")
    zip_code: str = Field(description="Zip code")
    residing_in_addr_since_years: int = Field(description="Number of years residing in the address")
    residing_in_addr_since_months: int = Field(description="Number of months residing in the address")
    own_house: bool = Field(description="Whether the individual owns the house or not")
    rented_house: bool = Field(description="Whether the individual rents the house or not")
    rent: float = Field(description="Rent amount")
    mailing_address_different: bool = Field(description="Whether the mailing address is different from the current "
                                                        "address or not")


class EmploymentDetails(BaseModel):
    business_owner_or_self_employed: bool = Field(description="Whether the individual is a business owner or "
                                                              "self-employed")
    ownership_of_25_pct_or_more: bool = Field(description="Whether the individual owns 25% or more of a business")


class DriverLicense(BaseModel):
    number: str = Field(description="Number of the driver's license")
    issue_date: datetime = Field(description="Issue date of the driver's license. The field name of the issue date is "
                                             "sometimes abbreviated as ISS. Do not pick up the expiry date for this "
                                             "field"
                                             "name, which is later than the issue date.")
    expiration_date: datetime = Field(description="Expiration date of the driver's license")
    issue_state: str = Field(description="State of issue of the driver's license in its full form")
    last_name: str = Field(description="Last name on the driver's license")
    first_name: str = Field(description="First name on the driver's license")
    dob: datetime = Field(description="Date of birth on the driver's license")


class Form1003(BaseModel):
    personal_details: PersonalDetails = Field(description="Personal details of the individual")
    extra_details: ExtraDetails = Field(description="Extra details of the individual")
    current_address: CurrentAddress = Field(description="Current address of the individual")
    employment_details: EmploymentDetails = Field(description="Employment details of the individual")
    license: DriverLicense = Field(description="Driver's license details of the individual")


def error_exit(error_message):
    print(error_message)
    sys.exit(1)


def process_1003_information(extracted_text):
    preamble = ("What you are seeing is a filled out 1003 loan application form. Your job is to extract the "
                "information from it accurately.")
    postamble = "Do not include any explanation in the reply. Only include the extracted information in the reply."
    system_template = "{preamble}"
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = "{format_instructions}\n\n{extracted_text}\n\n{postamble}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    parser = PydanticOutputParser(pydantic_object=Form1003)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    request = chat_prompt.format_prompt(preamble=preamble,
                                        format_instructions=parser.get_format_instructions(),
                                        extracted_text=extracted_text,
                                        postamble=postamble).to_messages()
    chat = ChatOpenAI()
    response = chat(request, temperature=0.0)
    print(f"Response from LLM:\n{response.content}")
    return response.content


def extract_text_from_pdf(file_path, pages_list=None):
    llmw = LLMWhispererClient()
    try:
        result = llmw.whisper(file_path=file_path, pages_to_extract=pages_list)
        extracted_text = result["extracted_text"]
        return extracted_text
    except LLMWhispererClientException as e:
        error_exit(e)


def process_1003_pdf(file_path, pages_list=None):
    extracted_text = extract_text_from_pdf(file_path, pages_list)
    print(extracted_text)
    response = process_1003_information(extracted_text)


def main():
    load_dotenv()
    process_1003_pdf("assets/docs/Scanned Loan Application.pdf")


if __name__ == "__main__":
    main()