"""Plantilla LIA (Legitimate Interest Assessment) - art. 6.1.f RGPD.

Genera un documento Markdown con el análisis de interés legítimo para sourcing
de candidatos a partir de fuentes públicas. Lo necesitas como evidencia
documental ante una posible inspección AEPD.
"""

from datetime import date


def generate_lia(
    *,
    controller_name: str,
    controller_contact: str,
    project_name: str,
    countries: list[str],
    sources_used: list[str],
    retention_default_days: int,
    retention_extended_days: int,
) -> str:
    """Devuelve un LIA en Markdown listo para guardar/imprimir."""
    today = date.today().isoformat()

    return f"""# Evaluación de Interés Legítimo (LIA)
## {project_name}

**Responsable del tratamiento**: {controller_name}
**Contacto**: {controller_contact}
**Fecha del análisis**: {today}
**Base legal invocada**: Art. 6.1.f RGPD - Interés legítimo

---

## 1. Identificación del interés legítimo

El responsable lleva a cabo actividades de selección de personal por cuenta de
clientes empresariales, requiriendo identificar profesionales con perfiles
específicos en el mercado laboral. Esta actividad constituye un interés legítimo
económico y operativo, reconocido por el Considerando 47 RGPD que cita
expresamente el "marketing directo" y por extensión análoga las actividades
profesionales de prospección comercial y de talento, cuando se realizan sobre
datos públicos y con garantías adecuadas.

## 2. Test de necesidad

El tratamiento es necesario para alcanzar la finalidad porque:
- Los servicios de selección requieren identificar candidatos potenciales
- No existe alternativa menos intrusiva: solicitar consentimiento previo a una
  población indeterminada de profesionales antes de evaluar su perfil es
  operativamente imposible
- Solo se utilizan datos publicados deliberadamente por el propio interesado
  en perfiles profesionales públicos (LinkedIn, Bayt, Xing) o documentos
  publicados voluntariamente por él (CVs en webs personales/académicas)

## 3. Test de equilibrio (balancing test)

### Intereses del responsable
- Cumplir contrato con cliente empresarial
- Mantener actividad económica viable
- Identificar talento de forma eficiente

### Derechos e intereses del interesado
- Privacidad y protección de datos personales
- Expectativa razonable sobre el uso de sus datos públicos profesionales
- Derecho a no ser perfilado sin información

### Salvaguardas implementadas
1. **Solo fuentes públicas**: datos publicados por el propio interesado en
   contextos profesionales (perfiles laborales, CVs publicados, directorios
   profesionales)
2. **No se procesan categorías especiales** (art. 9 RGPD): el sistema bloquea
   técnicamente la inferencia o registro de salud, religión, orientación,
   ideología, origen étnico, afiliación sindical
3. **Retención limitada**: {retention_default_days} días por defecto,
   {retention_extended_days} días si proceso activo. Purga automática diaria.
4. **Derecho de oposición operativo**: canal claro para que el interesado
   ejerza su derecho de oposición (art. 21 RGPD), tras lo cual sus datos se
   eliminan en menos de 72h
5. **Información en primer contacto**: cualquier comunicación al candidato
   incluye identificación del responsable, finalidad, base legal, derechos
   y plazo de retención
6. **Minimización**: solo se almacenan datos relevantes para la evaluación
   profesional. No se descargan ni almacenan documentos completos (CVs PDF)
7. **No cesión a terceros sin base legal**: los datos no se ceden a clientes
   sin que medie consentimiento del candidato tras primer contacto

### Conclusión del balancing
Las salvaguardas implementadas, junto con el carácter público y profesional
de los datos tratados, hacen que el interés legítimo del responsable
**prevalezca** sobre los derechos e intereses del interesado, sin que se
produzca un menoscabo desproporcionado de éstos.

## 4. Países de tratamiento

{chr(10).join(f"- {c}" for c in countries)}

Para tratamientos fuera del EEE se aplican las garantías del Capítulo V RGPD
(decisiones de adecuación, cláusulas tipo o garantías equivalentes según país).

## 5. Fuentes de datos utilizadas

{chr(10).join(f"- {s}" for s in sources_used)}

## 6. Derechos del interesado

El interesado puede ejercer en cualquier momento:
- Acceso (art. 15)
- Rectificación (art. 16)
- Supresión (art. 17)
- Limitación (art. 18)
- Portabilidad (art. 20)
- **Oposición (art. 21)** - especialmente relevante en interés legítimo
- A no ser objeto de decisiones automatizadas (art. 22)

Canal: {controller_contact}

## 7. Revisión

Este LIA se revisa anualmente o ante cambios sustanciales en:
- Las fuentes utilizadas
- Las finalidades del tratamiento
- El marco legal aplicable
- Las salvaguardas técnicas

**Próxima revisión**: {today} + 12 meses
"""
