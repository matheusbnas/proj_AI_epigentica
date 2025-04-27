import json

class DataProcessor:
    @staticmethod
    def transform_to_slides(processed_data):
        """Transforma dados processados em formato adequado para slides."""
        slides = []
        
        # Slide de título
        slides.append({
            "type": "title",
            "title": "Análise Genética",
            "subtitle": processed_data.get("patient_info", {}).get("name", "")
        })
        
        # Informações do paciente
        if "patient_info" in processed_data:
            patient_info = processed_data["patient_info"]
            content = (
                f"Nome: {patient_info.get('name', '')}\n"
                f"Idade: {patient_info.get('age', '')}\n"
                f"Data: {patient_info.get('date', '')}"
            )
            slides.append({
                "type": "info",
                "title": "Informações do Paciente",
                "content": content
            })
        
        # Dados genéticos por seção
        for section in processed_data.get("genetic_data", []):
            content = "Genes analisados:\n"
            for gene in section.get("genes", []):
                content += f"• {gene}\n"
            content += f"\nObservações:\n{section.get('comments', '')}"
            
            slides.append({
                "type": "genetic_section",
                "title": section.get("category", "Análise Genética"),
                "content": content
            })
        
        # Recomendações
        if "recommendations" in processed_data:
            slides.append({
                "type": "recommendations",
                "title": "Recomendações",
                "content": processed_data["recommendations"]
            })
        
        return slides