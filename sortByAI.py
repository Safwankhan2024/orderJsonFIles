# ai_sorter.py
import os
import json
import argparse
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

def read_json_file(file_path):
    """Read and extract medical information from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        disease_name = data.get("disease", "")
        mcqs = data.get("mcqs", [])
        
        # Extract key topics from first few questions for context
        key_topics = []
        for i, mcq in enumerate(mcqs[:3]):
            question = mcq.get("question", "")
            if question:
                key_topics.append(question[:100] + "..." if len(question) > 100 else question)
        
        return {
            "filename": Path(file_path).name,
            "path": str(file_path),
            "disease": disease_name,
            "key_concepts": key_topics,
            "question_count": len(mcqs)
        }
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None

def prepare_medical_sorting_prompt(files_info):
    """Create a textbook-based prompt for DeepSeek API."""
    
    prompt = f"""You are a medical education expert specializing in pediatric surgery curriculum design.

Sort these {len(files_info)} pediatric surgery MCQ files according to STANDARD PEDIATRIC SURGERY TEXTBOOK STRUCTURE:

**ORGANIZATION:**
1. BASIC PRINCIPLES (first)
   - Embryology fundamentals
   - Clinical outcomes/quality improvement
   - Ethical considerations
   - Anesthesia
   - Nutrition support

2. REGION/SYSTEM-BASED SECTIONS (after basic principles)
   - HEAD & NECK (torticollis, neck cysts, salivary glands)
   - CHEST (congenital chest wall deformities, lung/mediastinal cysts, diaphragmatic hernia)
   - CARDIOVASCULAR (neonatal CV physiology, ECLS, heart transplantation)
   - TRAUMA (abdominal trauma, burns, CNS injuries, vascular injury, splenic trauma)
   - ONCOLOGY (neuroblastoma, Wilms tumor, liver tumors, bone tumors, brain tumors, RMS, lymphoma, teratomas, ovarian/testicular tumors)
   - GASTROINTESTINAL TRACT
     * Esophagus: congenital anomalies, GERD, caustic strictures, replacement
     * Stomach: pyloric stenosis
     * Small intestine: atresia, malrotation, Meckel's, Crohn's
     * Large intestine: Hirschsprung's, ulcerative colitis, colonic atresia
     * Anorectal: malformations
   - LIVER/BILIARY (choledochal cyst, gallbladder disease, liver infections, jaundiced infant)
   - PANCREAS (annular pancreas)
   - ABDOMINAL WALL (defects, umbilical disorders, hernias)
   - ACUTE ABDOMEN (appendicitis, intussusception, NEC)
   - GENITOURINARY
     * Kidney: agenesis, dysplasia, ectopia, VUR, Wilms
     * Ureter: UPJ obstruction, megaureter
     * Bladder: exstrophy, neuropathic bladder
     * Urethra: hypospadias, posterior valves
     * Testis: undescended, torsion, tumors
   - VASCULAR ANOMALIES
   - TRANSPLANTATION (liver, kidney, intestine)

File details to sort:
{json.dumps(files_info, indent=2)}

Return ONLY a JSON object:
{{"sorted_files": ["mcq_json/01_filename.json", "mcq_json/02_filename.json", ...]}}"""
    
    return prompt

def sort_with_deepseek_api(files_info, api_key, base_url="https://api.deepseek.com"):
    """Use DeepSeek API to intelligently sort based on medical content."""
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    prompt = prepare_medical_sorting_prompt(files_info)
    
    try:
        print("🤖 Analyzing medical content with DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Medical curriculum design expert. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("sorted_files", [])
        
    except Exception as e:
        print(f"⚠️  API Error: {e}")
        print("📉 Falling back to filename-based sorting...")
        return fallback_sort(files_info)

def fallback_sort(files_info):
    """Sort by numeric prefix in filename as fallback."""
    sorted_by_number = sorted(files_info, key=lambda x: int(x["filename"].split('_')[0]))
    return [info["path"] for info in sorted_by_number]

def validate_sorting(sorted_files, files_info):
    """Ensure all files are included in sorted list."""
    original_files = {info["filename"]: info["path"] for info in files_info}
    validated = []
    
    for file_path in sorted_files:
        filename = Path(file_path).name
        if filename in original_files:
            validated.append(original_files[filename])
    
    # Add any missing files
    if len(validated) != len(files_info):
        missing = set(original_files.keys()) - set(Path(p).name for p in validated)
        for filename in missing:
            validated.append(original_files[filename])
            print(f"⚠️  Added missing file: {filename}")
    
    return validated

def generate_order_file(sorted_files, output_folder, output_name="order.txt"):
    """Generate the final order.txt file."""
    order_file_path = Path(output_folder) / output_name
    
    with open(order_file_path, 'w') as f:
        for index, file_path in enumerate(sorted_files, start=1):
            filename = Path(file_path).name
            f.write(f"{index:02d}_{filename}\n")
    
    return order_file_path

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="AI-powered medical MCQ sorter")
    parser.add_argument("--api-key", help="DeepSeek API key (optional if in .env)")
    parser.add_argument("--folder", default="E:\\kindle\\orderJsonFIles", help="Root folder")
    parser.add_argument("--output", default="order.txt", help="Output filename")
    parser.add_argument("--base-url", default="https://api.deepseek.com", help="API base URL")
    
    args = parser.parse_args()
    
    # Get API key from args, then env, then error
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ No API key found!")
        print("   • Add --api-key argument, OR")
        print("   • Create .env file with: DEEPSEEK_API_KEY=your_key_here")
        print("   • Get key from: https://platform.deepseek.com")
        return
    
    # Setup paths
    root_folder = Path(args.folder)
    mcq_folder = root_folder / "mcq_json"
    
    if not mcq_folder.exists():
        print(f"❌ mcq_json folder not found at {mcq_folder}")
        return
    
    # Scan and read JSON files
    json_files = list(mcq_folder.glob("*.json"))
    print(f"📁 Found {len(json_files)} JSON files")
    
    files_info = []
    for json_file in json_files:
        info = read_json_file(json_file)
        if info:
            files_info.append(info)
    
    if not files_info:
        print("❌ No valid files could be read")
        return
    
    print(f"✅ Extracted content from {len(files_info)} files")
    
    # Show sample
    print(f"\n📋 Sample analysis:")
    for info in files_info[:3]:
        print(f"  • {info['filename']}: {info['disease']} ({info['question_count']} questions)")
    
    # AI sorting
    print("\n" + "="*70)
    sorted_files = sort_with_deepseek_api(files_info, api_key, args.base_url)
    final_files = validate_sorting(sorted_files, files_info)
    
    # Generate order file
    order_path = generate_order_file(final_files, mcq_folder, args.output)
    
    print("="*70 + "\n")
    print(f"✅ Order file created: {order_path}")
    print(f"📊 Total files sorted: {len(final_files)}")
    
    # Preview
    print(f"\n🎯 Top 15 sorted files:")
    print("-" * 80)
    for i, file_path in enumerate(final_files[:15], 1):
        filename = Path(file_path).name
        disease = next(f["disease"] for f in files_info if f["filename"] == filename)
        print(f"{i:03d}. {filename:<60} → {disease}")

if __name__ == "__main__":
    main()