import json

class DataProcessor:
    @staticmethod
    def transform_to_slides(processed_data):
        slides = []
        
        # Informações do paciente
        slides.append({
            "type": "patient_info",
            "title": "Informações do Paciente",
            "content": processed_data["patient_info"],
            "url": None
        })
        
        # Dados genéticos
        for section in processed_data.get("genetic_data", []):
            slides.append({
                "type": "genetic_section",
                "category": section["category"],
                "genes": section["genes"],
                "comments": section["comments"],
                "url": None
            })
        
        # Recomendações nutricionais
        if processed_data.get("recommendations"):
            slides.append({
                "type": "recommendations",
                "content": processed_data["recommendations"],
                "url": None
            })
        
        return slides