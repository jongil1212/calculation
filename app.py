import streamlit as st
import re
from fractions import Fraction

# -----------------------------
# 기본 유틸 함수
# -----------------------------

BLANK_FEEDBACK = "답안을 적지 않았습니다. 답안을 작성해주세요."

def normalize_text(text: str) -> str:
    """답안 비교를 위한 기본 정규화"""
    if text is None:
        return ""
    text = text.strip()
    text = text.replace("＋", "+").replace("－", "-")
    text = text.replace("×", "*").replace("÷", "/")
    text = text.replace(" ", "")
    text = text.replace(",", ",")
    return text


def normalize_korean_text(text: str) -> str:
    """서술형 의미 채점을 위한 한글 답안 정규화"""
    if text is None:
        return ""
    text = text.strip()
    text = text.replace("＋", "+").replace("－", "-")
    text = text.replace("×", "*").replace("÷", "/")
    text = re.sub(r"\s+", "", text)
    return text


def contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def parse_fraction_value(expr: str):
    """
    간단한 수 표현을 Fraction으로 변환.
    예: -6/3, +1/2, 3.6, -2, 10
    """
    expr = normalize_text(expr)
    expr = expr.replace("+", "")

    try:
        if "/" in expr:
            return Fraction(expr)
        if "." in expr:
            return Fraction(expr)
        return Fraction(int(expr), 1)
    except Exception:
        return None


def extract_number_values(text: str):
    """
    답안에서 숫자 표현을 추출해 Fraction 값 목록으로 반환.
    """
    text = normalize_text(text)

    # 혼동 방지를 위해 부등호, 쉼표, 줄바꿈 등을 구분자로 사용
    candidates = re.findall(r"[+-]?\d+(?:\.\d+)?(?:/\d+)?", text)

    values = []
    raw_items = []

    for c in candidates:
        v = parse_fraction_value(c)
        if v is not None:
            values.append(v)
            raw_items.append(c)

    return values, raw_items


def has_wrong_extra_values(answer_values, correct_values):
    """정답 외 숫자가 포함되어 있는지 확인"""
    correct_set = set(correct_values)
    return any(v not in correct_set for v in answer_values)


def count_correct_values(answer_values, correct_values):
    return len(set(answer_values).intersection(set(correct_values)))


# -----------------------------
# 1번 채점
# -----------------------------

def grade_q1_1(answer: str):
    """
    1-(1) 음수 찾기
    정답: -4, -3/5, -6/3
    3개 모두 정확하면 1점
    2개 정확하면 0.5점
    정답 3개를 모두 썼지만 오답이 1~2개 추가된 경우 0.5점
    """
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK    
    values, raw = extract_number_values(answer)

    correct = [Fraction(-4, 1), Fraction(-3, 5), Fraction(-2, 1)]
    correct_count = count_correct_values(values, correct)
    has_extra = has_wrong_extra_values(values, correct)

    base_feedback = "음수는 부호에 -가 붙은 수를 의미합니다."

    if correct_count == 3 and not has_extra:
        return 1.0, f"음수 3개 중 3개를 찾았습니다. {base_feedback}"
    elif correct_count == 3 and has_extra:
        return 0.5, f"음수 3개 중 3개를 찾았지만, 음수가 아닌 수가 함께 포함되어 있습니다. {base_feedback}"
    elif correct_count == 2:
        return 0.5, f"음수 3개 중 2개를 찾았습니다. {base_feedback}"
    elif correct_count == 1:
        return 0.0, f"음수 3개 중 1개를 찾았습니다. {base_feedback}"
    else:
        return 0.0, f"음수 3개 중 0개를 찾았습니다. {base_feedback}"


def grade_q1_2(answer: str):
    """
    1-(2) 정수가 아닌 유리수 찾기
    정답: +1/2, -3/5, 3.6
    주의: -6/3 = -2 이므로 정수가 아닌 유리수가 아님
    3개 모두 정확하면 1점
    2개 정확하면 0.5점
    정답 3개를 모두 썼지만 오답이 1~2개 추가된 경우 0.5점
    """
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK    
    values, raw = extract_number_values(answer)

    correct = [Fraction(1, 2), Fraction(-3, 5), Fraction(18, 5)]
    correct_count = count_correct_values(values, correct)
    has_extra = has_wrong_extra_values(values, correct)

    has_minus_two = Fraction(-2, 1) in values

    if correct_count == 3 and not has_extra:
        return 1.0, "정수가 아닌 유리수 3개를 모두 정확히 찾았습니다."
    elif correct_count == 3 and has_extra:
        if has_minus_two:
            return 0.5, "정수가 아닌 유리수 3개를 모두 찾았지만, -6/3을 함께 포함했습니다. -6/3은 계산하면 -2이므로 정수입니다."
        return 0.5, "정수가 아닌 유리수 3개를 모두 찾았지만, 정수가 아닌 유리수가 아닌 수가 함께 포함되어 있습니다."
    elif correct_count == 2:
        if has_minus_two:
            return 0.5, "정수가 아닌 유리수 3개 중 2개를 찾았습니다. 다만 -6/3은 계산하면 -2이므로 정수입니다."
        return 0.5, "정수가 아닌 유리수 3개 중 2개를 찾았습니다."
    elif correct_count == 1:
        return 0.0, "정수가 아닌 유리수 3개 중 1개를 찾았습니다."
    else:
        return 0.0, "정수가 아닌 유리수 3개 중 0개를 찾았습니다."


def grade_q1_3(answer: str):
    """
    1-(3) 절댓값이 같은 두 수
    정답: +2, -6/3 또는 +2, -2
    답만 쓰면 인정
    """
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK
    values, raw = extract_number_values(answer)

    required = {Fraction(2, 1), Fraction(-2, 1)}

    if required.issubset(set(values)):
        # 두 수 외에 추가 숫자가 많으면 오답 처리
        if all(v in required for v in values):
            return 1.0, "절댓값이 같은 두 수를 정확히 찾았습니다."
        else:
            return 0.0, "정답 외의 다른 수가 함께 포함되어 있습니다."
    return 0.0, "절댓값이 같은 두 수를 정확히 찾지 못했습니다."


def grade_q1_4(answer: str):
    """
    1-(4) 부등호를 이용하여 작은 수부터 나열
    정답 순서:
    -4 < -6/3 또는 -2 < -3/5 < 0 < 1/2 < 2 < 3.6 < 10

    부등호 사용 + 순서 정확: 1점
    순서 정확하나 쉼표 등 사용: 0.5점
    """
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK    
    text = normalize_text(answer)
    values, raw = extract_number_values(answer)

    correct_order = [
        Fraction(-4, 1),
        Fraction(-2, 1),
        Fraction(-3, 5),
        Fraction(0, 1),
        Fraction(1, 2),
        Fraction(2, 1),
        Fraction(18, 5),
        Fraction(10, 1),
    ]

    has_all_and_only = len(values) == 8 and values == correct_order
    uses_inequality = "<" in text

    # 부등호 방향을 반대로 쓰는 경우 방지
    uses_wrong_direction = ">" in text and "<" not in text

    if has_all_and_only and uses_inequality:
        return 1.0, "부등호를 사용하여 작은 수부터 바르게 나열했습니다."
    elif has_all_and_only and not uses_inequality and not uses_wrong_direction:
        return 0.5, "순서는 맞지만 부등호를 사용하지 않았습니다."
    else:
        return 0.0, "수의 순서가 틀렸거나 빠진 수 또는 추가한 수가 있습니다."


def grade_q1(answers: dict):
    scores = {}
    feedback = {}

    graders = {
        "1-(1)": grade_q1_1,
        "1-(2)": grade_q1_2,
        "1-(3)": grade_q1_3,
        "1-(4)": grade_q1_4,
    }

    total = 0
    for key, func in graders.items():
        score, msg = func(answers.get(key, ""))
        scores[key] = score
        feedback[key] = msg
        total += score

    return total, scores, feedback


# -----------------------------
# 2번 채점
# -----------------------------

def grade_q2_1_calc(answer: str):
    """
    2-(1) 계산 수정: 5 + (-6) ÷ 2 = 2
    """
    text = normalize_korean_text(answer)

    blank_feedback = "계산 결과를 적지 않았습니다. 내가 생각하는 올바른 계산을 작성해주세요."

    if text == "":
        return 0.0, blank_feedback

    correct_patterns = [
        r"5\+\(-?6\)/2=2",
        r"5\+-6/2=2",
        r"5\+\(-3\)=2",
        r"=2",
        r"답은?2",
    ]

    wrong_patterns = [
        r"=-?1/2",
        r"=-?0\.5",
        r"=-1",
        r"=-?11",
    ]

    if contains_any(text, wrong_patterns):
        return 0.0, "계산 결과를 다시 확인해봅시다."

    if contains_any(text, correct_patterns):
        return 1.0, "올바른 계산 결과를 제시했습니다."

    return 0.0, blank_feedback


def grade_q2_1_reason(answer: str):
    """
    2-(1) 이유 설명: 나눗셈을 덧셈보다 먼저 해야 함
    용어 없이 의미가 맞으면 인정
    """
    text = normalize_korean_text(answer)

    retry_feedback = "덧셈, 뺄셈, 곱셈, 나눗셈이 혼합된 식에서 무엇부터 계산해야 했는지 생각해봅시다."

    has_division = contains_any(text, [
        r"나눗셈", r"나누기", r"몫", r"/", r"÷"
    ])

    has_first = contains_any(text, [
        r"먼저", r"우선", r"앞서", r"부터", r"먼저계산"
    ])

    misconception = contains_any(text, [
        r"왼쪽부터", r"순서대로만", r"더하기를먼저", r"덧셈을먼저"
    ])

    if misconception and not (has_division and has_first):
        return 0.0, retry_feedback

    if has_division and has_first:
        return 1.0, "나눗셈을 먼저 해야 한다는 이유를 설명했습니다."

    return 0.0, retry_feedback


def grade_q2_2_calc(answer: str):
    """
    2-(2) 계산 수정: 5×(-6)-2×(-3)=-24
    """
    text = normalize_korean_text(answer)

    blank_feedback = "계산 결과를 적지 않았습니다. 내가 생각하는 올바른 계산을 작성해주세요."

    if text == "":
        return 0.0, blank_feedback

    if "-24" in text:
        return 1.0, "올바른 계산 결과를 제시했습니다."

    wrong_patterns = [
        r"-32", r"-36", r"32", r"36", r"-28"
    ]

    if contains_any(text, wrong_patterns):
        return 0.0, "계산 결과를 다시 확인해봅시다."

    return 0.0, blank_feedback


def grade_q2_2_reason(answer: str):
    """
    2-(2) 이유 설명: 곱셈을 뺄셈보다 먼저 해야 함
    """
    text = normalize_korean_text(answer)

    retry_feedback = "덧셈, 뺄셈, 곱셈, 나눗셈이 혼합된 식에서 무엇부터 계산해야 했는지 생각해봅시다."

    has_multiplication = contains_any(text, [
        r"곱셈", r"곱하기", r"곱", r"\*", r"×"
    ])

    has_first = contains_any(text, [
        r"먼저", r"우선", r"앞서", r"부터", r"먼저계산"
    ])

    misconception = contains_any(text, [
        r"왼쪽부터", r"순서대로만", r"뺄셈을먼저", r"빼기를먼저"
    ])

    if misconception and not (has_multiplication and has_first):
        return 0.0, retry_feedback

    if has_multiplication and has_first:
        return 1.0, "곱셈을 먼저 해야 한다는 이유를 설명했습니다."

    return 0.0, retry_feedback


def grade_q2(answer_1: str, answer_2: str):
    scores = {}
    feedback = {}

    s, f = grade_q2_1_calc(answer_1)
    scores["2-(1) 계산"] = s
    feedback["2-(1) 계산"] = f

    s, f = grade_q2_1_reason(answer_1)
    scores["2-(1) 이유"] = s
    feedback["2-(1) 이유"] = f

    s, f = grade_q2_2_calc(answer_2)
    scores["2-(2) 계산"] = s
    feedback["2-(2) 계산"] = f

    s, f = grade_q2_2_reason(answer_2)
    scores["2-(2) 이유"] = s
    feedback["2-(2) 이유"] = f

    return sum(scores.values()), scores, feedback


# -----------------------------
# 3번 채점
# -----------------------------

def grade_q3_person(answer: str):
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK

    text = normalize_korean_text(answer)

    if "건우" in text:
        return 1.0, "옳은 사람으로 건우를 선택했습니다."
    return 0.0, "옳은 사람 판단이 명확하지 않거나 틀렸습니다."


def grade_q3_power_sign(answer: str):
    """
    이유 설명: -2^4 = -16 이므로 음수
    (-2)^4 = 16으로 해석한 답안은 오답 처리
    """
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK
    text = normalize_korean_text(answer)

    # 강한 오개념 차단
    wrong_patterns = [
        r"-2\^4=16",
        r"\(-2\)\^4=16.*그래서",
        r"2\^4=16.*양수",
        r"거듭제곱.*항상양수",
        r"-2의4제곱.*16"
    ]

    if contains_any(text, wrong_patterns) and "음수" not in text:
        return 0.0, "-2^4를 양수로 해석한 오개념이 있습니다."

    correct_patterns = [
        r"-2\^4=-16",
        r"-\(2\^4\)=-16",
        r"-16",
        r"-2\^4.*음수",
        r"음수"
    ]

    if contains_any(text, correct_patterns):
        return 1.0, "-2^4가 음수라는 점을 설명했습니다."

    return 0.0, "-2^4가 음수라는 설명이 부족합니다."


def grade_q3_product_sign(answer: str):
    """
    음수의 개수와 곱의 부호 설명
    '음수가 2개이기 때문'이라는 의미만 있어도 인정
    """
    if answer.strip() == "":
        return 0.0, BLANK_FEEDBACK
    text = normalize_korean_text(answer)

    has_two_negatives = contains_any(text, [
        r"음수2개",
        r"음수가2개",
        r"음수두개",
        r"음수두개",
        r"음수와음수",
        r"마이너스.*마이너스",
        r"부호가.*2개"
    ])

    has_positive = contains_any(text, [
        r"양수",
        r"\+",
        r"플러스"
    ])

    wrong_direction = contains_any(text, [
        r"음수1개",
        r"음수가1개",
        r"홀수개",
        r"음수가홀수",
        r"결과.*음수",
        r"부호.*음수"
    ])

    if wrong_direction and not has_two_negatives:
        return 0.0, "곱셈에서 음수의 개수와 부호 사이의 관계를 추가적으로 작성해줘야 좋은 답안이 됩니다."

    if has_two_negatives:
        return 1.0, "음수가 2개라는 점을 바르게 설명했습니다."

    if has_positive and not has_two_negatives:
        return 0.0, "곱셈에서 음수의 개수와 부호 사이의 관계를 추가적으로 작성해줘야 좋은 답안이 됩니다."

    return 0.0, "곱셈에서 음수의 개수와 부호 사이의 관계를 추가적으로 작성해줘야 좋은 답안이 됩니다."


def grade_q3_split(q3_person: str, q3_reason: str):
    scores = {}
    feedback = {}

    if q3_person.strip() == "":
        person_score = 0.0
        person_feedback = BLANK_FEEDBACK
    else:
        person_score, person_feedback = grade_q3_person(q3_person)

    if q3_reason.strip() == "":
        reason_score = 0.0
        reason_feedback = BLANK_FEEDBACK
    else:
        power_score, power_feedback = grade_q3_power_sign(q3_reason)
        product_score, product_feedback = grade_q3_product_sign(q3_reason)

        reason_score = power_score + product_score

        reason_feedback_parts = []

        if power_score == 1.0:
            reason_feedback_parts.append("-2^4의 부호를 바르게 판단했습니다.")
        else:
            reason_feedback_parts.append("-2^4가 어떤 부호인지 다시 생각해봅시다.")

        if product_score == 1.0:
            reason_feedback_parts.append("음수의 개수와 곱의 부호 관계를 바르게 설명했습니다.")
        else:
            reason_feedback_parts.append("곱셈에서 음수의 개수와 부호 사이의 관계를 추가적으로 작성해줘야 좋은 답안이 됩니다.")

        reason_feedback = " ".join(reason_feedback_parts)

    scores["옳은 사람 판단(1점)"] = person_score
    feedback["옳은 사람 판단(1점)"] = person_feedback

    scores["이유 설명(2점)"] = reason_score
    feedback["이유 설명(2점)"] = reason_feedback

    return sum(scores.values()), scores, feedback


# -----------------------------
# 4번 채점
# -----------------------------

def text_has_equivalent_expression(text: str, required_tokens: list[str]) -> bool:
    """
    식 세우기용 간단 검사.
    required_tokens에 있는 핵심 토큰이 모두 들어 있으면 식을 인정.
    """
    t = normalize_korean_text(text)
    return all(token in t for token in required_tokens)


def extract_score_value(answer: str):
    """
    학생 최종 점수 답안에서 대표 숫자 하나를 추출.
    여러 개가 있으면 마지막 숫자를 최종값으로 간주.
    """
    values, raw = extract_number_values(answer)
    if not values:
        return None
    return values[-1]


def grade_expression(answer: str, student: str):
    text = normalize_korean_text(answer)

    required = {
        "진호": ["2", "*3", "/1/2", "-3/2"],
        "해인": ["-1", "/2", "*-1/4", "-3/2"],
        "승혜": ["1", "/2", "*3", "+7"],
        "민섭": ["-3", "*-1/4", "/1/2", "+7"],
    }

    # 사용자가 ×, ÷, 분수 표기를 다양하게 쓰므로 별도 패턴으로 완화
    patterns = {
        "진호": [
            r"2.*(\*3|곱하기3|×3).*(/1/2|나누기1/2|÷1/2).*(-3/2|빼기3/2)"
        ],
        "해인": [
            r"-1.*(/2|나누기2|÷2).*(\*-1/4|곱하기-1/4|×-1/4).*(-3/2|빼기3/2)"
        ],
        "승혜": [
            r"1.*(/2|나누기2|÷2).*(\*3|곱하기3|×3).*(\+7|더하기7)"
        ],
        "민섭": [
            r"-3.*(\*-1/4|곱하기-1/4|×-1/4).*(/1/2|나누기1/2|÷1/2).*(\+7|더하기7)"
        ],
    }

    for p in patterns[student]:
        if re.search(p, text):
            return 1.0, f"{student}의 이동 경로에 맞는 식을 세웠습니다."

    return 0.0, f"{student}의 식이 이동 경로와 맞지 않거나 핵심 연산이 빠졌습니다."


def grade_final_score(answer: str, correct_value: Fraction, student: str):
    value = extract_score_value(answer)

    if value == correct_value:
        return 1.0, f"{student}의 최종 점수를 정확히 구했습니다."

    return 0.0, f"{student}의 최종 점수가 정확하지 않습니다."


def grade_q4_final_choice(jinho_ans, haein_ans, seunghye_ans, minseop_ans, final_answer):
    """
    마지막 판단:
    정답 점수 기준 해인 선택: 1점
    계산 오류가 있어도 자신이 제시한 네 점수 중 가장 작은 학생을 선택: 0.5점
    """
    if final_answer.strip() == "":
        return 0.0, BLANK_FEEDBACK

    final_text = normalize_korean_text(final_answer)

    correct_values = {
        "진호": Fraction(21, 2),
        "해인": Fraction(-11, 8),
        "승혜": Fraction(17, 2),
        "민섭": Fraction(17, 2),
    }

    if "해인" in final_text:
        return 1.0, "가장 작은 점수의 학생인 해인을 선택했습니다."

    # 학생이 각 답안에 쓴 최종값을 추출해서 그 기준의 최솟값과 비교
    student_answers = {
        "진호": extract_score_value(jinho_ans),
        "해인": extract_score_value(haein_ans),
        "승혜": extract_score_value(seunghye_ans),
        "민섭": extract_score_value(minseop_ans),
    }

    # 네 학생 점수가 모두 제시되어야 0.5점 가능
    if any(v is None for v in student_answers.values()):
        return 0.0, "네 학생의 최종 점수가 모두 제시되지 않아 비교 판단을 인정하기 어렵습니다."

    min_student = min(student_answers, key=lambda name: student_answers[name])

    if min_student in final_text:
        return 0.5, "정답과 다른 학생을 골랐지만, 자신이 구한 점수 중 가장 작은 학생을 선택했습니다."

    return 0.0, "가장 작은 점수의 학생 판단이 올바르지 않습니다."


def grade_q4(jinho_ans, haein_ans, seunghye_ans, minseop_ans, final_answer):
    scores = {}
    feedback = {}

    correct_scores = {
        "진호": Fraction(21, 2),
        "해인": Fraction(-11, 8),
        "승혜": Fraction(17, 2),
        "민섭": Fraction(17, 2),
    }

    answers = {
        "진호": jinho_ans,
        "해인": haein_ans,
        "승혜": seunghye_ans,
        "민섭": minseop_ans,
    }

    for student, ans in answers.items():
        if ans.strip() == "":
            scores[f"4 {student} 식"] = 0.0
            feedback[f"4 {student} 식"] = BLANK_FEEDBACK

            scores[f"4 {student} 최종점수"] = 0.0
            feedback[f"4 {student} 최종점수"] = BLANK_FEEDBACK
        else:
            s, f = grade_expression(ans, student)
            scores[f"4 {student} 식"] = s
            feedback[f"4 {student} 식"] = f

            s, f = grade_final_score(ans, correct_scores[student], student)
            scores[f"4 {student} 최종점수"] = s
            feedback[f"4 {student} 최종점수"] = f

    s, f = grade_q4_final_choice(
        jinho_ans,
        haein_ans,
        seunghye_ans,
        minseop_ans,
        final_answer
    )
    scores["4 간식 학생 판단"] = s
    feedback["4 간식 학생 판단"] = f

    return sum(scores.values()), scores, feedback

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="정수와 유리수 자동 채점기",
    page_icon="📘",
    layout="centered"
)

# -----------------------------
# 세션 상태 초기화
# -----------------------------

default_values = {
    "q1_1": "",
    "q1_2": "",
    "q1_3": "",
    "q1_4": "",

    "q2_1": "",
    "q2_2": "",
    "q2_1_solution": "",
    "q2_1_reason": "",
    "q2_2_solution": "",
    "q2_2_reason": "",

    "q3": "",
    "q3_person": "",
    "q3_reason": "",
    "q4_jinho": "",
    "q4_haein": "",
    "q4_seunghye": "",
    "q4_minseop": "",
    "q4_final": "",
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------
# 일반 수식 입력기
# -----------------------------

def append_to_answer(target_key, value):
    """선택한 기호나 수식을 답안 입력칸 뒤에 추가"""
    current = st.session_state.get(target_key, "")
    st.session_state[target_key] = current + value


def backspace_answer(target_key):
    """답안 입력칸에서 마지막 글자 삭제"""
    current = st.session_state.get(target_key, "")
    st.session_state[target_key] = current[:-1]


def clear_answer(target_key):
    """답안 입력칸 전체 삭제"""
    st.session_state[target_key] = ""


def insert_fraction(target_key, numerator_key, denominator_key, negative_key):
    """분자와 분모를 이용해 분수 입력"""
    numerator = st.session_state.get(numerator_key, "").strip()
    denominator = st.session_state.get(denominator_key, "").strip()
    is_negative = st.session_state.get(negative_key, False)

    if numerator == "" or denominator == "":
        return

    if is_negative:
        fraction_text = f"-{numerator}/{denominator}"
    else:
        fraction_text = f"{numerator}/{denominator}"

    append_to_answer(target_key, fraction_text)


def insert_power(target_key, base_key, exponent_key, negative_key):
    """밑과 지수를 이용해 거듭제곱 입력"""
    base = st.session_state.get(base_key, "").strip()
    exponent = st.session_state.get(exponent_key, "").strip()
    is_negative = st.session_state.get(negative_key, False)

    if base == "" or exponent == "":
        return

    if is_negative:
        power_text = f"-{base}^{exponent}"
    else:
        power_text = f"{base}^{exponent}"

    append_to_answer(target_key, power_text)


def general_math_input(target_key, label="수식 입력기"):
    """
    학생용 일반 수식 입력기.
    특정 문제의 정답 숫자를 제시하지 않고, 학생이 직접 숫자·분수·거듭제곱을 조합할 수 있게 함.
    """
    with st.expander(label, expanded=False):
        st.caption("버튼을 누르면 답안 입력칸 뒤에 자동으로 추가됩니다.")

        st.markdown("##### 숫자")
        num_cols = st.columns(10)
        for i in range(10):
            with num_cols[i]:
                st.button(
                    str(i),
                    key=f"{target_key}_num_{i}",
                    on_click=append_to_answer,
                    args=(target_key, str(i))
                )

        st.markdown("##### 기호")
        symbols = [
            ("+", "+"),
            ("−", "-"),
            ("×", "×"),
            ("÷", "÷"),
            ("=", "="),
            ("<", "<"),
            (">", ">"),
            ("(", "("),
            (")", ")"),
            (".", "."),
        ]

        sym_cols = st.columns(10)
        for i, (btn_label, value) in enumerate(symbols):
            with sym_cols[i]:
                st.button(
                    btn_label,
                    key=f"{target_key}_sym_{i}",
                    on_click=append_to_answer,
                    args=(target_key, value)
                )

        st.markdown("##### 분수 만들기")

        numerator_key = f"{target_key}_fraction_numerator"
        denominator_key = f"{target_key}_fraction_denominator"
        fraction_negative_key = f"{target_key}_fraction_negative"

        frac_col1, frac_col2, frac_col3, frac_col4 = st.columns([2, 2, 1, 2])

        with frac_col1:
            st.text_input(
                "분자",
                key=numerator_key,
            )

        with frac_col2:
            st.text_input(
                "분모",
                key=denominator_key,
            )

        with frac_col3:
            st.checkbox(
                "음수",
                key=fraction_negative_key
            )

        with frac_col4:
            st.button(
                "분수 넣기",
                key=f"{target_key}_insert_fraction",
                on_click=insert_fraction,
                args=(target_key, numerator_key, denominator_key, fraction_negative_key)
            )

        st.markdown("##### 거듭제곱 만들기")

        base_key = f"{target_key}_power_base"
        exponent_key = f"{target_key}_power_exponent"
        power_negative_key = f"{target_key}_power_negative"

        pow_col1, pow_col2, pow_col3, pow_col4 = st.columns([2, 2, 1, 2])

        with pow_col1:
            st.text_input(
                "밑",
                key=base_key,
            )

        with pow_col2:
            st.text_input(
                "지수",
                key=exponent_key,
            )

        with pow_col3:
            st.checkbox(
                "앞에 -",
                key=power_negative_key
            )

        with pow_col4:
            st.button(
                "거듭제곱 넣기",
                key=f"{target_key}_insert_power",
                on_click=insert_power,
                args=(target_key, base_key, exponent_key, power_negative_key)
            )

        st.markdown("##### 수정")
        edit_col1, edit_col2 = st.columns(2)

        with edit_col1:
            st.button(
                "⌫ 한 글자 지우기",
                key=f"{target_key}_backspace",
                on_click=backspace_answer,
                args=(target_key,)
            )

        with edit_col2:
            st.button(
                "전체 지우기",
                key=f"{target_key}_clear",
                on_click=clear_answer,
                args=(target_key,)
            )

# -----------------------------
# 답안 수식 미리보기
# -----------------------------

def simple_expr_to_latex(text):
    """
    학생이 입력한 간단한 수식 문자열을 LaTeX 형태로 변환.
    채점에는 영향을 주지 않고, 화면 미리보기용으로만 사용.
    """
    if text is None:
        return ""

    expr = text.strip()

    if expr == "":
        return ""

    # 기본 기호 정리
    expr = expr.replace("×", r"\times ")
    expr = expr.replace("÷", r"\div ")
    expr = expr.replace("*", r"\times ")

    # 공백 정리
    expr = expr.replace(" ", "")

    # 부등호 주변 간격
    expr = expr.replace("<", r" < ")
    expr = expr.replace(">", r" > ")
    expr = expr.replace("=", r" = ")

    # 거듭제곱: -2^4, 2^4 등을 LaTeX로 변환
    expr = re.sub(
        r"(-?\d+)\^(\d+)",
        r"\1^{\2}",
        expr
    )

    # 분수 변환
    # 예: -1/2 -> -\frac{1}{2}, 3/5 -> \frac{3}{5}
    expr = re.sub(
        r"(?<!\d)(-?\d+)\/(\d+)(?!\d)",
        lambda m: (
            r"-\frac{" + m.group(1)[1:] + "}{" + m.group(2) + "}"
            if m.group(1).startswith("-")
            else r"\frac{" + m.group(1) + "}{" + m.group(2) + "}"
        ),
        expr
    )

    return expr


def show_answer_preview(target_key, label="입력한 답안 수식 미리보기"):
    """
    답안칸에 입력된 내용을 LaTeX로 미리 보여줌.
    """
    answer = st.session_state.get(target_key, "").strip()

    if answer:
        st.caption(label)
        st.latex(simple_expr_to_latex(answer))

def is_completed(keys):
    """해당 문항의 답안 입력 여부 확인"""
    return all(st.session_state.get(k, "").strip() for k in keys)
def is_all_blank(keys):
    """해당 문제의 답안칸이 모두 비어 있는지 확인"""
    return all(st.session_state.get(k, "").strip() == "" for k in keys)


def reset_answers():
    for key in default_values:
        st.session_state[key] = ""


# -----------------------------
# 상단 제목 영역
# -----------------------------

st.markdown(
    """
    <div style="padding: 10px 0 5px 0;">
        <h1 style="font-size: 32px; margin-bottom: 8px;">✏️ 정수와 유리수 서·논술형 답안 작성 연습</h1>
        <p style="font-size: 16px; line-height: 1.7; color: #374151;">
            작성한 답안을 입력한 뒤 문제의 조건에 맞게 작성하였는지 확인하세요.
            수업 시간에 배운 정수와 유리수의 개념, 계산 순서, 부호 판단, 대소 비교를 복습할 수 있습니다.
            서술형 답안 작성 참고용으로 활용하세요. 😊
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()
st.info(
    "수식을 직접 입력하기 어렵다면 각 답안칸 아래의 '수식 입력기'를 열어 숫자, 분수, 거듭제곱을 만들어 입력할 수 있습니다."
)

# -----------------------------
# 진행률 표시
# -----------------------------

completed_count = 0

if is_completed(["q1_1", "q1_2", "q1_3", "q1_4"]):
    completed_count += 1
if is_completed(["q2_1_solution", "q2_1_reason", "q2_2_solution", "q2_2_reason"]):
    completed_count += 1
if is_completed(["q3_person", "q3_reason"]):
    completed_count += 1
if is_completed(["q4_jinho", "q4_haein", "q4_seunghye", "q4_minseop", "q4_final"]):
    completed_count += 1

total_problem_count = 4
progress_value = completed_count / total_problem_count

col_progress, col_reset = st.columns([4, 1])

with col_progress:
    st.markdown(f"✅ 완료된 문제: **{completed_count} / {total_problem_count}**")
    st.progress(progress_value)

with col_reset:
    st.button("🔄 처음부터", on_click=reset_answers)

st.markdown(
    """
    <p style="font-size: 14px; color: #6B7280;">
        문제를 선택해 답안을 작성하세요. 모든 답안을 작성한 뒤 아래의 
        <b>전체 채점하기</b> 버튼을 누르면 세부 점수와 피드백을 확인할 수 있습니다.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# -----------------------------
# 탭 구성
# -----------------------------

tab1, tab2, tab3, tab4, tab_review = st.tabs(
    ["문제 1", "문제 2", "문제 3", "문제 4", "📚 복습할 내용"]
)

# -----------------------------
# 문제 1
# -----------------------------

with tab1:
    st.subheader("문제 1. 정수와 유리수의 분류와 대소 관계")

    st.info("보기의 숫자들에 대해 질문에 답하시오.")

    st.latex(
        r"-4,\quad 0,\quad +\frac{1}{2},\quad -\frac{3}{5},\quad +2,\quad 3.6,\quad 10,\quad -\frac{6}{3}"
    )

    st.markdown("**(1) 음수를 모두 찾으시오. [1점]**")
    st.text_input(
        "1-(1) 답안 입력",
        key="q1_1",
        label_visibility="collapsed"
    )
    show_answer_preview("q1_1")
    general_math_input("q1_1")

    st.markdown("**(2) 정수가 아닌 유리수를 모두 찾으시오. [1점]**")
    st.text_input(
        "1-(2) 답안 입력",
        key="q1_2",
        label_visibility="collapsed"
    )
    show_answer_preview("q1_2")
    general_math_input("q1_2")

    st.markdown("**(3) 절댓값이 같은 두 수를 모두 찾으시오. [1점]**")
    st.text_input(
        "1-(3) 답안 입력",
        key="q1_3",
        label_visibility="collapsed"
    )
    show_answer_preview("q1_3")
    general_math_input("q1_3")

    st.markdown("**(4) 부등호를 이용하여 위의 수를 작은 것부터 순서대로 나열하시오. [1점]**")
    st.text_input(
        "1-(4) 답안 입력",
        key="q1_4",
        label_visibility="collapsed"
    )
    show_answer_preview("q1_4")
    general_math_input("q1_4")

    if st.button("제출", key="grade_q1_button", use_container_width=False):
        if is_all_blank(["q1_1", "q1_2", "q1_3", "q1_4"]):
            st.warning("답변을 작성하고 제출해주세요.")
        else:
            q1_total, q1_scores, q1_feedback = grade_q1({
                "1-(1)": st.session_state.q1_1,
                "1-(2)": st.session_state.q1_2,
                "1-(3)": st.session_state.q1_3,
                "1-(4)": st.session_state.q1_4,
            })

            st.success(f"문제 1 점수: {q1_total} / 4점")

            result_rows = []
            for key in q1_scores:
                result_rows.append({
                    "채점 항목": key,
                    "점수": q1_scores[key],
                    "피드백": q1_feedback[key]
                })

            st.dataframe(result_rows, use_container_width=True, hide_index=True)
    
# -----------------------------
# 문제 2
# -----------------------------

with tab2:
    st.subheader("문제 2. 계산 순서 오류 수정하기")

    # -----------------------------
    # 2-(1)
    # -----------------------------
    st.markdown("**(1) 현우의 풀이를 보고, 틀린 부분이 있다면 고치고 그 이유를 쓰시오. [2점]**")

    with st.container(border=True):
        st.markdown("**현우의 풀이**")
        st.latex(r"5+(-6)\div2=(-1)\div2=-\frac{1}{2}")

    col_q2_1_a, col_q2_1_b = st.columns(2)

    with col_q2_1_a:
        st.markdown("**나의 풀이**")
        st.text_area(
            "2-(1) 나의 풀이",
            key="q2_1_solution",
            height=170,
            label_visibility="collapsed"
        )
        show_answer_preview("q2_1_solution")
        general_math_input("q2_1_solution")

    with col_q2_1_b:
        st.markdown("**수정한 이유**")
        st.text_area(
            "2-(1) 수정한 이유",
            key="q2_1_reason",
            height=170,
            label_visibility="collapsed"
        )

    st.divider()

    # -----------------------------
    # 2-(2)
    # -----------------------------
    st.markdown("**(2) 지수의 풀이를 보고, 틀린 부분이 있다면 고치고 그 이유를 쓰시오. [2점]**")

    with st.container(border=True):
        st.markdown("**지수의 풀이**")
        st.latex(r"5\times(-6)-2\times(-3)=(-30)-2\times(-3)=(-32)\times(-3)=96")

    col_q2_2_a, col_q2_2_b = st.columns(2)

    with col_q2_2_a:
        st.markdown("**나의 풀이**")
        st.text_area(
            "2-(2) 나의 풀이",
            key="q2_2_solution",
            height=170,
            label_visibility="collapsed"
        )
        show_answer_preview("q2_2_solution")
        general_math_input("q2_2_solution")

    with col_q2_2_b:
        st.markdown("**수정한 이유**")
        st.text_area(
            "2-(2) 수정한 이유",
            key="q2_2_reason",
            height=170,
            label_visibility="collapsed"
        )

    st.markdown("")

    # 문제 2 개별 채점 버튼
    if st.button("제출", key="grade_q2_button", use_container_width=False):
        if is_all_blank([
            "q2_1_solution",
            "q2_1_reason",
            "q2_2_solution",
            "q2_2_reason"
        ]):
            st.warning("답변을 작성하고 제출해주세요.")
        else:
            q2_1_combined = (
                st.session_state.q2_1_solution
                + " "
                + st.session_state.q2_1_reason
            )

            q2_2_combined = (
                st.session_state.q2_2_solution
                + " "
                + st.session_state.q2_2_reason
            )

            q2_total, q2_scores, q2_feedback = grade_q2(
                q2_1_combined,
                q2_2_combined
            )

            st.success(f"문제 2 점수: {q2_total} / 4점")

            result_rows = []
            for key in q2_scores:
                result_rows.append({
                    "채점 항목": key,
                    "점수": q2_scores[key],
                    "피드백": q2_feedback[key]
                })

            st.dataframe(result_rows, use_container_width=True, hide_index=True)
    
# -----------------------------
# 문제 3
# -----------------------------

with tab3:
    st.subheader("문제 3. 거듭제곱과 부호 판단")

    # 문제 제시 상자
    with st.container(border=True):
        st.markdown(
            """
            다음은 건우와 은서가 아래 식을 계산하는 방법을 각각 설명한 것입니다.
            """
        )
        st.latex(r"\left(-\frac{1}{6}\right)\times(-2^4)")
        st.markdown("누구의 방법이 옳은지 판단하고, 그 이유를 설명하시오. [3점]")

    col_gunwoo, col_eunseo = st.columns(2)

    with col_gunwoo:
        with st.container(border=True):
            st.markdown("**건우**")
            st.markdown("음수가 2개이니까 다음과 같이 계산해야 해.")
            st.latex(r"+\left(\frac{1}{6}\times2^4\right)")

    with col_eunseo:
        with st.container(border=True):
            st.markdown("**은서**")
            st.markdown("음수가 5개이니까 다음과 같이 계산해야 해.")
            st.latex(r"-\left(\frac{1}{6}\times2^4\right)")

    st.markdown("")

    col_q3_a, col_q3_b = st.columns(2)

    with col_q3_a:
        st.markdown("**옳은 방법을 설명한 사람**")
        st.text_input(
            "3번 옳은 사람",
            key="q3_person",
            label_visibility="collapsed"
        )

    with col_q3_b:
        st.markdown("**이유**")
        st.text_area(
            "3번 이유",
            key="q3_reason",
            height=180,
            label_visibility="collapsed"
        )
        show_answer_preview("q3_reason")
        general_math_input("q3_reason")

    st.markdown("")

    # 문제 3 개별 채점 버튼
    if st.button("제출", key="grade_q3_button", use_container_width=False):
        if is_all_blank(["q3_person", "q3_reason"]):
            st.warning("답변을 작성하고 제출해주세요.")
        else:
            q3_combined = (
                st.session_state.q3_person
                + " "
                + st.session_state.q3_reason
            )

            q3_total, q3_scores, q3_feedback = grade_q3_split(
                st.session_state.q3_person,
                st.session_state.q3_reason
            )

            st.success(f"문제 3 점수: {q3_total} / 3점")

            result_rows = []
            for key in q3_scores:
                result_rows.append({
                    "채점 항목": key,
                    "점수": q3_scores[key],
                    "피드백": q3_feedback[key]
                })

            st.dataframe(result_rows, use_container_width=True, hide_index=True)
    
# -----------------------------
# 문제 4
# -----------------------------

with tab4:
    st.subheader("문제 4. 사다리 계산 게임")

    with st.container(border=True):
        st.markdown(
            """
            진호, 해인, 승혜, 민섭이는 사다리 계산 게임을 했습니다.  
            가장 작은 수가 나오는 학생이 간식을 사기로 했습니다.  
            각 학생의 계산 식과 최종 점수를 구하고, 간식을 사게 될 학생을 판단하시오. [9점]
            """
        )

        st.image("problem4.png", use_container_width=True)

    st.markdown("")

        # 답안 입력: 1행 - 진호 | 해인
    col_q4_1, col_q4_2 = st.columns(2)

    with col_q4_1:
        st.markdown("**진호의 계산식과 최종 점수**")
        st.text_area(
            "진호의 식과 최종 점수",
            key="q4_jinho",
            height=140,
            label_visibility="collapsed"
        )
        show_answer_preview("q4_jinho")
        general_math_input("q4_jinho")

    with col_q4_2:
        st.markdown("**해인의 계산식과 최종 점수**")
        st.text_area(
            "해인의 식과 최종 점수",
            key="q4_haein",
            height=140,
            label_visibility="collapsed"
        )
        show_answer_preview("q4_haein")
        general_math_input("q4_haein")

    st.markdown("")

    # 답안 입력: 2행 - 승혜 | 민섭
    col_q4_3, col_q4_4 = st.columns(2)

    with col_q4_3:
        st.markdown("**승혜의 계산식과 최종 점수**")
        st.text_area(
            "승혜의 식과 최종 점수",
            key="q4_seunghye",
            height=140,
            label_visibility="collapsed"
        )
        show_answer_preview("q4_seunghye")
        general_math_input("q4_seunghye")

    with col_q4_4:
        st.markdown("**민섭의 계산식과 최종 점수**")
        st.text_area(
            "민섭의 식과 최종 점수",
            key="q4_minseop",
            height=140,
            label_visibility="collapsed"
        )
        show_answer_preview("q4_minseop")
        general_math_input("q4_minseop")

    st.markdown("")

    # 최종 판단
    st.markdown("**간식을 사게 될 학생**")
    st.text_input(
        "최종 판단 입력",
        key="q4_final",
        label_visibility="collapsed"
    )
    
    st.markdown("")

    if st.button("제출", key="grade_q4_button", use_container_width=False):
        if is_all_blank([
            "q4_jinho",
            "q4_haein",
            "q4_seunghye",
            "q4_minseop",
            "q4_final"
        ]):
            st.warning("답변을 작성하고 제출해주세요.")
        else:
            q4_total, q4_scores, q4_feedback = grade_q4(
                st.session_state.q4_jinho,
                st.session_state.q4_haein,
                st.session_state.q4_seunghye,
                st.session_state.q4_minseop,
                st.session_state.q4_final
            )

            st.success(f"문제 4 점수: {q4_total} / 9점")

            result_rows = []
            for key in q4_scores:
                result_rows.append({
                    "채점 항목": key,
                    "점수": q4_scores[key],
                    "피드백": q4_feedback[key]
                })

            st.dataframe(result_rows, use_container_width=True, hide_index=True)
        
# -----------------------------
# 복습할 내용
# -----------------------------

with tab_review:
    st.subheader("📚 복습할 내용")

    st.markdown(
        """
        문제를 풀기 전에 헷갈리는 부분을 확인하거나, 채점 후 틀린 부분을 다시 복습하세요.
        """
    )

    with st.expander("1. 음수, 정수, 유리수"):
        st.markdown(
            """
            - **음수**는 0보다 작은 수입니다.
            - **정수**는 ..., -3, -2, -1, 0, 1, 2, 3, ... 과 같은 수입니다.
            - **유리수**는 분수로 나타낼 수 있는 수입니다.
            - 정수가 아닌 유리수에는 분수나 유한소수 등이 포함됩니다.
            - 예를 들어 `-6/3`은 분수 모양이지만 계산하면 `-2`이므로 정수입니다.
            """
        )

    with st.expander("2. 절댓값"):
        st.markdown(
            """
            - 절댓값은 수직선에서 0으로부터 떨어진 거리입니다.
            - `+2`와 `-2`는 방향은 다르지만 0으로부터의 거리가 같으므로 절댓값이 같습니다.
            - `-6/3 = -2`이므로 `+2`와 `-6/3`은 절댓값이 같습니다.
            """
        )

    with st.expander("3. 정수와 유리수의 대소 관계"):
        st.markdown(
            """
            - 음수는 0보다 작고, 양수는 0보다 큽니다.
            - 음수끼리는 절댓값이 클수록 더 작은 수입니다.
            - 예: `-4 < -2 < -3/5 < 0`
            - 문제에서 부등호를 이용하라고 했으면 쉼표가 아니라 `<` 또는 `>`를 사용해야 합니다.
            """
        )

    with st.expander("4. 사칙계산 순서"):
        st.markdown(
            """
            - 괄호가 있으면 괄호 안을 먼저 계산합니다.
            - 거듭제곱이 있으면 거듭제곱을 먼저 계산합니다.
            - 곱셈과 나눗셈은 덧셈과 뺄셈보다 먼저 계산합니다.
            - 같은 단계의 계산은 왼쪽에서 오른쪽으로 계산합니다.
            """
        )

    with st.expander("5. 거듭제곱과 부호"):
        st.markdown(
            """
            - `-2^4`는 `-(2^4)`를 뜻하므로 `-16`입니다.
            - `(-2)^4`는 `(-2)×(-2)×(-2)×(-2)`이므로 `16`입니다.
            - 이 문제에서는 `-2^4`가 사용되었으므로 음수로 판단해야 합니다.
            """
        )

    with st.expander("6. 음수의 곱셈"):
        st.markdown(
            """
            - 음수 × 음수 = 양수
            - 음수 × 양수 = 음수
            - 음수의 개수가 짝수 개이면 결과는 양수입니다.
            - 음수의 개수가 홀수 개이면 결과는 음수입니다.
            """
        )

st.divider()

# -----------------------------
# 전체 채점 버튼 및 결과
# -----------------------------

st.subheader("🧮 전체 채점")

if st.button("전체 채점하기", type="primary", use_container_width=True):
    q1_total, q1_scores, q1_feedback = grade_q1({
        "1-(1)": st.session_state.q1_1,
        "1-(2)": st.session_state.q1_2,
        "1-(3)": st.session_state.q1_3,
        "1-(4)": st.session_state.q1_4,
    })

    q2_1_combined = (
        st.session_state.q2_1_solution
        + " "
        + st.session_state.q2_1_reason
    )

    q2_2_combined = (
        st.session_state.q2_2_solution
        + " "
        + st.session_state.q2_2_reason
    )

    q2_total, q2_scores, q2_feedback = grade_q2(
        q2_1_combined,
        q2_2_combined
    )

    q3_combined = (
        st.session_state.q3_person
        + " "
        + st.session_state.q3_reason
    )

    q3_total, q3_scores, q3_feedback = grade_q3(
        q3_combined
    )

    q4_total, q4_scores, q4_feedback = grade_q4(
        st.session_state.q4_jinho,
        st.session_state.q4_haein,
        st.session_state.q4_seunghye,
        st.session_state.q4_minseop,
        st.session_state.q4_final
    )

    total_score = q1_total + q2_total + q3_total + q4_total

    all_scores = {}
    all_feedback = {}

    all_scores.update(q1_scores)
    all_scores.update(q2_scores)
    all_scores.update(q3_scores)
    all_scores.update(q4_scores)

    all_feedback.update(q1_feedback)
    all_feedback.update(q2_feedback)
    all_feedback.update(q3_feedback)
    all_feedback.update(q4_feedback)

    st.success(f"총점: {total_score} / 20점")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("1번", f"{q1_total} / 4")
    with col_b:
        st.metric("2번", f"{q2_total} / 4")
    with col_c:
        st.metric("3번", f"{q3_total} / 3")
    with col_d:
        st.metric("4번", f"{q4_total} / 9")

    st.markdown("### 세부 채점 결과")

    result_rows = []
    for key in all_scores:
        result_rows.append({
            "채점 항목": key,
            "점수": all_scores[key],
            "피드백": all_feedback[key]
        })

    st.dataframe(result_rows, use_container_width=True, hide_index=True)

    st.info(
        "자동 채점 결과는 참고용입니다. 식을 말로 설명하거나 표현 방식이 특이한 경우에는 선생님의 최종 확인이 필요합니다."
    )
