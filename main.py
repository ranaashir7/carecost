import sys
import requests
from dotenv import load_dotenv
import os
import openai
import json

load_dotenv()

url = os.getenv("BASE_URL")

def search_icd10_codes(symptom):
    params = {
        "sf": "code,name",     # fields to return
        "terms": symptom,       # search term
        "maxList": 10            # maximum number of results to return (changed from 1 to 10)
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data[3]

def generate_description(code, name):
    prompt = (
        f"Explain the ICD-10 code {code}: {name} in simple, layman-friendly terms "
        "in 1-2 sentences. Avoid medical jargon."
    )
    
    response = openai.chat.completions.create(
        model="gpt-4.1",  # Using valid model name
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=100,  # Adjusted to a reasonable length for explanations
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

def icd_to_cpt(icd_code, diagnosis):
    prompt = (
        f"A patient is diagnosed with ICD-10 code {icd_code}: {diagnosis}.\n"
        "List the most common CPT codes used for evaluation or treatment of this condition in an outpatient setting.\n"
        "Provide a concise list of all codes without explanations.\n"
        "Format the response in the following JSON format. DO NOT PROVIDE ANYTHING BUT THE JSON:\n"
        "{\n"
        "    \"diagnosis\": \"{ICD-10 code}: {diagnosis}\",\n"
        "    \"CPT_categories\": [\n"
        "        {\"category\": \"{Category Name}\", \"codes\": [\"{CPT code 1}\", \"{CPT code 2}\", \"{CPT code 3}\"]},\n"
        "        {\"category\": \"{Category Name}\", \"codes\": [\"{CPT code 1}\", \"{CPT code 2}\", \"{CPT code 3}\"]}\n"
        "    ]\n"
        "}"
    )

    response = openai.chat.completions.create(
        model="gpt-4.1",  # Using valid model name
        messages=[{"role": "user", "content": prompt}],
        temperature=0 
    )

    return response.choices[0].message.content.strip()

def get_cpt_prices_from_model(cpt_code, zip_code):
    """
    Get CPT code prices from the OpenAI model.
    
    Args:
        cpt_code (str): The CPT code to get prices for.
        
    Returns:
        dict: A dictionary containing in-network and out-of-network prices.
    """
    
    # Define the prompt for the model

    system_prompt = (
        "You are an expert in medical coding and billing. "
        "Your job is to provide accurate pricing for CPT codes based on a given zip code in the US. "
        "You always respond in a precise JSON format without ranges or explanations."
    )


    user_prompt = (
        f"Provide the in-network and out-of-network prices for CPT code {cpt_code} "
        f"in zip code {zip_code}.\n"
        "Format the response strictly as:\n"
        "{\n"
        "    \"in_network_price\": \"$XXX.XX\",\n"
        "    \"out_of_network_price\": \"$XXX.XX\"\n"
        "}\n"
        "Provide realistic prices in USD format with dollar signs."
    )

    # Call the OpenAI API to get the prices
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    # Extract the content from the response
    content = response.choices[0].message.content.strip()
    
    # Parse the JSON content to extract prices
    try:
        parsed_response = json.loads(content)
        # Debug: print the actual response structure
        print(f"    Debug - Raw response for {cpt_code}: {parsed_response}")
        return parsed_response
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {content}")
        return {
            "in_network_price": "undefined",
            "out_of_network_price": "undefined"
        }

def parse_price(price_str):
    """
    Parse price string and return numeric value
    
    Args:
        price_str (str): Price string like "$1,234" or "undefined"
    
    Returns:
        float: Numeric price value or None if undefined
    """
    if price_str == "undefined" or not price_str:
        return None
    
    # Remove $ and commas, then convert to float
    try:
        return float(price_str.replace("$", "").replace(",", ""))
    except (ValueError, AttributeError):
        return None

def is_valid_zip(zip_code):
    """
    Check if the provided zip code is valid (5 digits).
    
    Args:
        zip_code (str): The zip code to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    res = requests.get(f"https://api.zippopotam.us/us/{zip_code}")
    return res.status_code == 200

def get_icd10_codes_with_descriptions(symptom):
    """
    Get ICD-10 codes for a symptom with AI-generated descriptions.
    
    Args:
        symptom (str): The symptom to search for
        
    Returns:
        list: List of dictionaries containing code, name, and description
    """
    matches = search_icd10_codes(symptom)
    if not matches:
        return []
    
    results = []
    for code, name in matches:
        try:
            explanation = generate_description(code, name)
            results.append({
                "code": code,
                "name": name,
                "description": explanation
            })
        except Exception as e:
            print(f"Error generating description for {code}: {e}")
            results.append({
                "code": code,
                "name": name,
                "description": "Description unavailable"
            })
    
    return results

def get_cpt_codes_for_diagnosis(icd_code, diagnosis_name):
    """
    Get CPT codes for a given ICD-10 diagnosis.
    
    Args:
        icd_code (str): The ICD-10 code
        diagnosis_name (str): The diagnosis name
        
    Returns:
        dict: Parsed JSON containing diagnosis and CPT categories, or None if error
    """
    try:
        cpt_codes_json = icd_to_cpt(icd_code, diagnosis_name)
        return json.loads(cpt_codes_json)
    except Exception as e:
        print(f"Error getting CPT codes for {icd_code}: {e}")
        return None

def calculate_cost_analysis(cpt_categories, zip_code):
    """
    Calculate comprehensive cost analysis for CPT categories.
    
    Args:
        cpt_categories (list): List of CPT categories from get_cpt_codes_for_diagnosis
        zip_code (str): Valid zip code for pricing
        
    Returns:
        dict: Comprehensive cost analysis including category and overall ranges
    """
    if not is_valid_zip(zip_code):
        raise ValueError("Invalid zip code provided")
    
    category_results = []
    
    for category in cpt_categories:
        category_name = category['category']
        category_in_network_prices = []
        category_out_network_prices = []
        cpt_details = []
        
        for cpt_code in category["codes"]:
            try:
                costs = get_cpt_prices_from_model(cpt_code, zip_code)
                
                # Handle different possible key names
                in_network_key = 'in_network_price' if 'in_network_price' in costs else 'in-network_price'
                out_network_key = 'out_of_network_price' if 'out_of_network_price' in costs else 'out-network_price'
                
                in_network_raw = costs.get(in_network_key, "undefined")
                out_network_raw = costs.get(out_network_key, "undefined")
                
                in_network_price = parse_price(in_network_raw)
                out_network_price = parse_price(out_network_raw)

                cpt_details.append({
                    "code": cpt_code,
                    "in_network_price": in_network_price,
                    "out_network_price": out_network_price,
                    "in_network_raw": in_network_raw,
                    "out_network_raw": out_network_raw
                })

                if in_network_price is not None:
                    category_in_network_prices.append(in_network_price)
                
                if out_network_price is not None:
                    category_out_network_prices.append(out_network_price)
                        
            except Exception as e:
                print(f"Error getting costs for {cpt_code}: {e}")
                cpt_details.append({
                    "code": cpt_code,
                    "in_network_price": None,
                    "out_network_price": None,
                    "in_network_raw": "error",
                    "out_network_raw": "error",
                    "error": str(e)
                })
        
        # Calculate category ranges
        category_in_range = None
        category_out_range = None
        
        if category_in_network_prices:
            category_in_range = {
                'min': min(category_in_network_prices),
                'max': max(category_in_network_prices)
            }
            
        if category_out_network_prices:
            category_out_range = {
                'min': min(category_out_network_prices),
                'max': max(category_out_network_prices)
            }
        
        category_results.append({
            'category': category_name,
            'cpt_details': cpt_details,
            'in_network_range': category_in_range,
            'out_network_range': category_out_range
        })
    
    # Calculate overall ranges
    in_network_ranges = [cat['in_network_range'] for cat in category_results if cat['in_network_range'] is not None]
    out_network_ranges = [cat['out_network_range'] for cat in category_results if cat['out_network_range'] is not None]
    
    overall_in_range = None
    overall_out_range = None
    
    if in_network_ranges:
        overall_in_range = {
            'min': sum(r['min'] for r in in_network_ranges),
            'max': sum(r['max'] for r in in_network_ranges),
            'category_count': len(in_network_ranges)
        }
        
    if out_network_ranges:
        overall_out_range = {
            'min': sum(r['min'] for r in out_network_ranges),
            'max': sum(r['max'] for r in out_network_ranges),
            'category_count': len(out_network_ranges)
        }
    
    return {
        'categories': category_results,
        'overall_in_network_range': overall_in_range,
        'overall_out_network_range': overall_out_range,
        'zip_code': zip_code
    }

def get_complete_cost_analysis(symptom, icd_selection_index, zip_code):
    """
    Complete end-to-end cost analysis for a symptom.
    
    Args:
        symptom (str): The symptom to analyze
        icd_selection_index (int): Index of the ICD-10 code to select (0-based)
        zip_code (str): Valid zip code for pricing
        
    Returns:
        dict: Complete analysis including ICD codes, CPT codes, and cost analysis
    """
    # Step 1: Get ICD-10 codes
    icd_codes = get_icd10_codes_with_descriptions(symptom)
    if not icd_codes:
        return {"error": "No matching ICD-10 codes found for the symptom"}
    
    # Step 2: Validate selection
    if icd_selection_index < 0 or icd_selection_index >= len(icd_codes):
        return {"error": f"Invalid selection index. Must be between 0 and {len(icd_codes)-1}"}
    
    selected_icd = icd_codes[icd_selection_index]
    
    # Step 3: Get CPT codes
    cpt_data = get_cpt_codes_for_diagnosis(selected_icd['code'], selected_icd['name'])
    if not cpt_data:
        return {"error": "Failed to get CPT codes for the selected diagnosis"}
    
    # Step 4: Calculate costs
    try:
        cost_analysis = calculate_cost_analysis(cpt_data['CPT_categories'], zip_code)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to calculate cost analysis: {str(e)}"}
    
    return {
        "symptom": symptom,
        "available_icd_codes": icd_codes,
        "selected_icd": selected_icd,
        "cpt_data": cpt_data,
        "cost_analysis": cost_analysis
    }

# chatbot where user can interact with a openai model to ask general medical questions (function will take in the user query and output the chatboyt response)
def chatbot(query):
    """
    Interact with OpenAI model to answer general medical questions.
    
    Args:
        query (str): User's question or query
        
    Returns:
        str: Response from the OpenAI model
    """
    system_prompt = (f"You are a medical expert. Answer the user's question in a clear and concise manner, "
                     "providing accurate medical information without unnecessary jargon.")

    
    response = openai.chat.completions.create(
        model="gpt-4.1",  # Using valid model name
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        max_completion_tokens=200,  # Adjusted for more detailed responses
        temperature=0.5  # Slightly higher temperature for more varied responses
    )
    
    return response.choices[0].message.content.strip()

# Example usage for testing
if __name__ == "__main__":
    # Interactive mode for testing
    symptom = input("Enter a symptom: ")
    
    # Get ICD codes
    icd_codes = get_icd10_codes_with_descriptions(symptom)
    if not icd_codes:
        print("No matching ICD-10 codes found.")
        exit()
    
    print(f"\nICD-10 codes for '{symptom}':\n")
    for i, icd in enumerate(icd_codes):
        print(f"{i+1}. {icd['code']}: {icd['name']}")
        print(f"   → {icd['description']}\n")
    
    # Get user selection
    while True:
        try:
            choice = int(input(f"Select a code (1-{len(icd_codes)}): "))
            if 1 <= choice <= len(icd_codes):
                selection_index = choice - 1
                break
            else:
                print(f"Please enter a number between 1 and {len(icd_codes)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Get zip code
    zip_code = input("Enter your zip code for cost lookup: ")
    while not is_valid_zip(zip_code):
        print("Invalid zip code. Please enter a valid 5-digit zip code.")
        zip_code = input("Enter your zip code for cost lookup: ")
    
    # Get complete analysis
    result = get_complete_cost_analysis(symptom, selection_index, zip_code)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nSelected: {result['selected_icd']['code']}: {result['selected_icd']['name']}")
        print("-" * 50)
        
        cost_analysis = result['cost_analysis']
        
        # Display category results
        for category in cost_analysis['categories']:
            print(f"Category: {category['category']}")
            
            if category['in_network_range']:
                print(f"In-Network Range: ${category['in_network_range']['min']:,.2f} - ${category['in_network_range']['max']:,.2f}")
            else:
                print("In-Network Range: No data available")
                
            if category['out_network_range']:
                print(f"Out-of-Network Range: ${category['out_network_range']['min']:,.2f} - ${category['out_network_range']['max']:,.2f}")
            else:
                print("Out-of-Network Range: No data available")
            
            print("-" * 30)
        
        # Display overall summary
        print("OVERALL COST SUMMARY:")
        print("=" * 50)
        
        if cost_analysis['overall_in_network_range']:
            overall_in = cost_analysis['overall_in_network_range']
            print(f"Overall In-Network Range: ${overall_in['min']:,.2f} - ${overall_in['max']:,.2f}")
            print(f"(Sum of {overall_in['category_count']} category ranges)")
        else:
            print("Overall In-Network Range: No data available")
            
        if cost_analysis['overall_out_network_range']:
            overall_out = cost_analysis['overall_out_network_range']
            print(f"Overall Out-of-Network Range: ${overall_out['min']:,.2f} - ${overall_out['max']:,.2f}")
            print(f"(Sum of {overall_out['category_count']} category ranges)")
        else:
            print("Overall Out-of-Network Range: No data available")
        
        print("=" * 50)