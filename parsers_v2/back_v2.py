from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import enum

app = FastAPI(
    title="OHS Expert Compliance Service API",
    description="MVP сервиса экспресс-аудита ЛНА по охране труда с учетом требований Приказа 772н и Постановления 2464"
)



class UserRole(str, enum.Enum):
    EXPERT = "expert"  # Линейный инженер (детальный аудит)
    ORGANIZER = "organizer"  # Руководитель службы ОТ (сводные отчеты)
    DIRECTOR = "director"  # Директор / ЛПР (риск-дашборд)



def verify_role(required_roles: List[UserRole]):
    def dependency(user_role: UserRole = UserRole.EXPERT):
        if user_role not in required_roles:
            raise HTTPException(status_code=403, detail="Действие запрещено для вашей роли доступа")
        return user_role

    return dependency



class SeverityLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"  # Прямой риск штрафа ГИТ или приостановки деятельности
    WARNING = "WARNING"  # Нарушение стандартов оформления (ГОСТ Р 7.0.97)
    RECOMMENDATION = "RECOMMEND"  # Советы по улучшению формулировок


class ValidationErrorItem(BaseModel):
    category: str
    severity: SeverityLevel
    message: str
    location: Optional[str] = None

# === 3. СХЕМЫ ДАННЫХ ===
class DocumentChunk(BaseModel):
    text: str
    font: str
    size: float
    page: Optional[int] = None


class ValidationRequest(BaseModel):
    doc_type: str  # "instruction", "journal", "checklist"
    document_data: List[DocumentChunk]



# А. Нормоконтроль оформления (ГОСТ Р 7.0.97-2016)
def validate_gost_7_0_97(chunks: List[DocumentChunk]) -> List[ValidationErrorItem]:
    errors = []
    for idx, chunk in enumerate(chunks):
        if len(chunk.text.strip()) < 3: continue

        # Нарушение шрифта — это WARNING (не влечет штраф ГИТ, но портит нормоконтроль)
        font_lower = chunk.font.lower()
        if "times" not in font_lower and "arial" not in font_lower:
            errors.append(ValidationErrorItem(
                category="Нормоконтроль",
                severity=SeverityLevel.WARNING,
                message=f"Нестандартный шрифт '{chunk.font}'. Рекомендован Times New Roman или Arial.",
                location=f"Стр. {chunk.page if chunk.page else idx}"
            ))
    return errors


# Б. Валидация Инструкций (Приказ Минтруда № 772н — К вопросу №14)
def validate_order_772n(chunks: List[DocumentChunk]) -> List[ValidationErrorItem]:
    errors = []
    full_text = " ".join([c.text.lower() for c in chunks])

    # 5 обязательных глав по закону
    required_chapters = {
        "общие требования": "Общие требования охраны труда",
        "перед началом работы": "Требования охраны труда перед началом работы",
        "во время работы": "Требования охраны труда во время работы",
        "в аварийных ситуациях": "Требования охраны труда в аварийных ситуациях",
        "по окончании работы": "Требования охраны труда по окончании работы"
    }

    for key, original_name in required_chapters.items():
        if key not in full_text:
            # Отсутствие главы — это CRITICAL (прямой штраф ч.1 ст. 5.27.1 КоАП)
            errors.append(ValidationErrorItem(
                category="Структура текста (Приказ 772н)",
                severity=SeverityLevel.CRITICAL,
                message=f"Отсутствует обязательный нормативный раздел: '{original_name}'"
            ))
    return errors


# В. Валидация Журналов (Постановление Правительства № 2464 — К вопросу №1)
def validate_journal_post_2464(chunks: List[DocumentChunk]) -> List[ValidationErrorItem]:
    errors = []
    full_text = " ".join([c.text.lower() for c in chunks])

    # Проверка структуры полей (ГОСТ 12.0.004-2015 + Пост. 2464)
    required_fields = ["фио", "дата", "подпись"]
    for field in required_fields:
        if field not in full_text:
            errors.append(ValidationErrorItem(
                category="Реквизиты документа",
                severity=SeverityLevel.CRITICAL,
                message=f"В форме фиксации инструктажа не найден обязательный столбец/поле: '{field.upper()}'"
            ))

    # Контроль сроков просрочки инструктажей (раз в 180 дней по Пост. 2464)
    for chunk in chunks:
        if len(chunk.text) == 10 and chunk.text.count(".") == 2:  # Шаблон даты ДД.ММ.ГГГГ
            try:
                date_obj = datetime.strptime(chunk.text, "%d.%m.%Y")
                if datetime.now() - date_obj > timedelta(days=180):
                    errors.append(ValidationErrorItem(
                        category="Сроки действия",
                        severity=SeverityLevel.CRITICAL,
                        message=f"Выявлен факт нарушения периодичности обучения! Инструктаж от {chunk.text} просрочен (более 6 месяцев)."
                    ))
            except ValueError:
                continue
    return errors



@app.post("/api/v1/verify/expert", response_model=Dict[str, Any])
async def expert_document_audit(
        request: ValidationRequest,
        role: UserRole = Depends(verify_role([UserRole.EXPERT, UserRole.ORGANIZER]))
):
    all_violations = []

    if request.doc_type == "instruction":
        all_violations.extend(validate_gost_7_0_97(request.document_data))
        all_violations.extend(validate_order_772n(request.document_data))
    elif request.doc_type == "journal":
        all_violations.extend(validate_journal_post_2464(request.document_data))
    else:
        raise HTTPException(status_code=400, detail="Указан неподдерживаемый тип документа (Шаблон не найден)")

    critical_count = sum(1 for v in all_violations if v.severity == SeverityLevel.CRITICAL)

    return {
        "status": "FAILED" if critical_count > 0 else "PASSED",
        "analyzed_at": datetime.now().isoformat(),
        "total_errors": len(all_violations),
        "violations": all_violations
    }


@app.get("/api/v1/dashboard/director")
async def director_risk_dashboard(
        role: UserRole = Depends(verify_role([UserRole.DIRECTOR]))
):

    return {
        "company_status": "HIGH_RISK",
        "compliance_score_percent": 68,
        "git_inspection_readiness": "Не готов",
        "financial_risk_estimation": "До 1 300 000 рублей (на основе ст. 5.27.1 КоАП за системные дефекты в журналах)",
        "recommendation": "Поручите руководителю службы ОТ проверить недостающие разделы в инструкциях по Приказу 772н."
    }