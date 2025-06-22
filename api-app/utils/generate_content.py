import os
import json
import pprint
from enum import Enum
from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from google.api_core.exceptions import GoogleAPIError


from data.templates.mock_data import content_gen_input

load_dotenv()

def generate_content(input_dict):

    input_json_string = json.dumps(input_dict, indent=4)
    final_prompt = base_prompt + input_json_string

    class MetricID(str, Enum):
        ndvi = "ndvi"
        vegetation_fraction = "vegetation_fraction"
        soil_fraction = "soil_fraction"
        precipitation = "precipitation"
        temperature = "temperature"
        curve_number = "curve_number"

    class MetricTitle(str, Enum):
        ndvi = "NORMALIZED DIFFERENCE VEGETATION INDEX"
        vegetation_fraction = "VEGETATION FRACTION"
        soil_fraction = "SOIL FRACTION"
        precipitation = "PRECIPITATION"
        temperature = "TEMPERATURE"
        curve_number = "CURVE NUMBER"


    class MetricDescription(str, Enum):
        ndvi = "Indicates vegetation health from 0 to 1."
        vegetation_fraction = "Proportion of ground covered by vegetation."
        soil_fraction = "Volumetric water content in the soil."
        precipitation = "Amount of rainfall in millimeters."
        temperature = "Average surface temperature in degrees Celsius."
        curve_number = "Runoff potential."

    class KeyInsight(BaseModel):
        title: str
        detail: str

    class SeriesItem(BaseModel):
        timestamp: str
        value: float

    class Metric(BaseModel):
        id: MetricID
        description: MetricDescription
        selected: bool
        title: MetricTitle
        mean_value: float
        mean_insight: str
        time_insight: str
        series: list[SeriesItem]

    class ReportContent(BaseModel):
        location: str
        time_period: str
        overview: str
        key_insights: list[KeyInsight]
        metrics: list[Metric]
        action_plan: list[str]

    try:
            api_key = os.getenv("GEMINI_API_TOKEN")
            if not api_key:
                raise EnvironmentError("GEMINI_API_TOKEN environment variable is not set.")

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=final_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ReportContent,
                }
            )

            print("✅ Content generated")
            
            # Convert to dictionary
            response_text = response.text  # This should be a JSON string
            try:
                data = json.loads(response_text)  # Convert to Python dict
            
                # Write the dict  to a debug file
                with open("debug_parsed_response.py", "w", encoding="utf-8") as debug_file:
                    pprint.pprint(data, stream=debug_file, indent=4, width=120) # Use pprint to write the dict

            except json.JSONDecodeError as e:
                print("❌ Failed to decode JSON:", e)
            
            return data

    except ValidationError as ve:
        print("❌ Pydantic validation error:", ve)
    except GoogleAPIError as ge:
        print("❌ Gemini API error:", ge)
    except EnvironmentError as ee:
        print("❌ Environment error:", ee)
    except Exception as e:
        print("❌ Unexpected error:", e)

base_prompt = r"""
You are an environmental analysis assistant specializing in vegetation dynamics and water-related ecosystem services. Your task is to analyze provided environmental monitoring data for a specific region and time period and generate a structured report in a predefined JSON format. This report will support environmental agencies, farmers, conservation organizations, and institutions.

**Knowledge base for the analysis**
The information is synthesized from research pertinent to the specified region and metrics.
NDVI: is a satellite-derived index that quantifies the greenness and density of vegetation. Significance for Analysis: Changes in NDVI over time are a strong indicator of land use/land cover change. A decreasing trend can signal deforestation, land degradation, or agricultural stress, while an increasing trend may indicate afforestation or favorable growing conditions.
Vegetation Fraction: This metric represents the proportion of the ground covered by green vegetation when viewed from above. It provides a direct measure of the extent of vegetation canopy. Relationship to other metrics: Vegetation fraction is closely related to NDVI but offers a more direct physical interpretation of cover. It directly influences the Curve Number (CN) as vegetative cover intercepts rainfall and promotes infiltration.
Soil Fraction: This metric represents the proportion of exposed soil in a given area. It is complementary to the vegetation fraction. Significance for Analysis: An increasing soil fraction over time, especially when coupled with a decreasing vegetation fraction, is a clear indicator of land degradation and heightened erosion risk.
Precipitation: The amount of rainfall received over a specific period. Significance for Analysis: Precipitation is the primary driver of surface runoff. Analyzing its temporal distribution and intensity is crucial for understanding changes in runoff potential and flood risk.
Temperature: The measure of atmospheric heat. Significance for Analysis: Long-term temperature trends can indicate climate change impacts on vegetation phenology and the hydrological cycle. Short-term temperature anomalies can lead to vegetation stress.
Curve Number (CN): The SCS-CN (Soil Conservation Service Curve Number) is an empirical parameter used to predict direct surface runoff from a rainfall event. The CN value is determined by the area's soil type, land use/land cover, and antecedent soil moisture conditions. Significance for Analysis: The Curve Number provides a powerful, integrated measure of how land cover changes impact runoff. An increase in the average CN for a region over time is a strong indicator of increased flood risk due to changes such as deforestation or urbanization. Conversely, a decrease in CN, perhaps due to afforestation, suggests an improvement in water regulation services.

**Input Template:**
You will receive environmental data in a JSON structure similar to the following example. The data contains metrics like 'ndvi', 'vegetation_fraction', 'soil-fraction', 'precipitation', 'temperature', and 'curve_number' for specific dates within a single region. Some metrics may be not be selected by the user.

```json
{
    "region": "District 1 - Ho Chi Minh",
    "outputs": {
        "2024-12-23": {
            "curve-number": 70.89308553051583,
            "ndvi": 0.3311726052982869,
            "precipitation": 1.1920928955078125e-10, // Note: this very small value should be interpreted as effectively zero
            "soil-fraction": 0.026419354124047587,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.8305334428763211
        },
        // ... potentially many more date entries ...
        "2025-01-27": {
            "curve-number": 71.94932288563587,
            "ndvi": 0.34504334964796574,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.21028195963685203,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.7823688578321615
        }
    }
}

**Output Data:**
Your job is to generate the report's content and fit them into the provided json schema. The data includes:
- location: The "region" value from the input data. Ideally at least 2 geographical identifiers in the name. For example: "DISTRICT 7 - HO CHI MINH"
- time_period: The start and end date as a string. For example: "10 APR - 35 MAY 2025"
- overview: Provide a concise summary of the overall environmental conditions and notable changes observed during the reporting period based on the input data. Highlight the general state of vegetation and water factors. Include the region and time period analyzed, the metrics included in the analysis, and the suggestions related to the action plan.
- key_insights: List the most significant findings or trends observed across the different metrics. Each insight should be a brief, actionable statement in a [{"title": Category, "detail": Insight Description}] json format (e.g., [{"title": "Healthy but Moderate Vegetation", "NDVI showed a slight decline towards the end of the period."}, {"title": "Seasonal Rainfall Distribution", "Precipitation remained negligible throughout the reporting period."}]).
- metrics: For each selected metric present in the input data ('ndvi', 'vegetation_fraction', 'soil-fraction', 'precipitation', 'temperature', and 'curve_number'):
- mean_value: Calculate the average value of the metric across all dates in the input data. Round up to 2 decimals.
- mean_insight: Interpret the calculated mean value. What does this average value suggest about the condition (e.g., "An average NDVI of X suggests moderate vegetation density," "An average curve number of Y indicates typical runoff potential for this area"). Relate it to the region's context if possible.
- time_insight: Analyze each metric value through the given time period and write a short paragraph of the time series insight gathered from the data. 
- action_plan: write a action plan as a list of potential action items that the stakeholers can take based on all the insights of the report.
- trend: A word to capture the trend of the time series.

**Input Data:**
Here is the input data you will analyze
"""


generate_content(content_gen_input)