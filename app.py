import streamlit as st
import re
from fractions import Fraction

# -----------------------------
# 기본 유틸 함수
# -----------------------------

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
    """
    values, raw = extract_number_values(answer)

    correct = [Fraction(-4, 1), Fraction(-3, 5), Fraction(-2, 1)]
    correct_count = count_correct_values(values, correct)

    if correct_count == 3 and not has_wrong_extra_values(values, correct):
        return 1.0, "음수 3개를 모두 정확히 찾았습니다."
    elif correct_count == 2:
        return 0.5, "음수 3개 중 2개를 정확히 찾았습니다."
    else:
        return 0.0, "음수 찾기가 부족하거나 오답이 많습니다."


def grade_q1_2(answer: str):
    """
    1-(2) 정수가 아닌 유리수 찾기
    정답: +1/2, -3/5, 3.6
    주의: -6/3 = -2 이므로 정수가 아닌 유리수가 아님
    """
    values, raw = extract_number_values(answer)

    correct = [Fraction(1, 2), Fraction(-3, 5), Fraction(18, 5)]
    correct_count = count_correct_values(values, correct)

    # -6/3 또는 -2를 포함한 경우는 대표 오개념
    has_minus_two = Fraction(-2, 1) in values

    if correct_count == 3 and not has_wrong_extra_values(values, correct):
        return 1.0, "정수가 아닌 유리수 3개를 모두 정확히 찾았습니다."
    elif correct_count == 2:
        if has_minus_two:
            return 0.5, "정답 2개를 찾았지만, -6/3을 정수가 아닌 유리수로 본 오개념이 있습니다."
        return 0.5, "정수가 아닌 유리수 3개 중 2개를 정확히 찾았습니다."
    else:
        return 0.0, "정수가 아닌 유리수 찾기가 부족하거나 오답이 많습니다."


def grade_q1_3(answer: str):
    """
    1-(3) 절댓값이 같은 두 수
    정답: +2, -6/3 또는 +2, -2
    답만 쓰면 인정
    """
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

    correct_patterns = [
        r"5\+\(-?6\)/2=2",
        r"5\+-6/2=2",
        r"5\+\(-3\)=2",
        r"=2",
        r"답은?2",
    ]

    # 오답 결과 차단
    wrong_patterns = [
        r"=-?1/2",
        r"=-?0\.5",
        r"=-1",
        r"=-?11",
    ]

    if contains_any(text, wrong_patterns):
        return 0.0, "계산 결과가 올바르지 않습니다."

    if contains_any(text, correct_patterns) or "2" in text:
        return 1.0, "올바른 계산 결과 2를 제시했습니다."

    return 0.0, "올바른 계산 결과 2가 명확하지 않습니다."


def grade_q2_1_reason(answer: str):
    """
    2-(1) 이유 설명: 나눗셈을 덧셈보다 먼저 해야 함
    용어 없이 의미가 맞으면 인정
    """
    text = normalize_korean_text(answer)

    has_division = contains_any(text, [
        r"나눗셈", r"나누기", r"몫", r"/", r"÷"
    ])

    has_first = contains_any(text, [
        r"먼저", r"우선", r"앞서", r"부터", r"먼저계산"
    ])

    has_addition_context = contains_any(text, [
        r"덧셈", r"더하기", r"\+", r"5\+"
    ])

    misconception = contains_any(text, [
        r"왼쪽부터", r"순서대로만", r"더하기를먼저", r"덧셈을먼저"
    ])

    if misconception and not (has_division and has_first):
        return 0.0, "계산 순서에 대한 오개념이 있습니다."

    if has_division and has_first:
        return 1.0, "나눗셈을 먼저 해야 한다는 이유를 설명했습니다."

    # '사칙연산 순서가 틀렸다'만 있는 경우는 의미가 불완전하므로 0 처리
    return 0.0, "나눗셈을 덧셈보다 먼저 해야 한다는 의미가 부족합니다."


def grade_q2_2_calc(answer: str):
    """
    2-(2) 계산 수정: 5×(-6)-2×(-3)=-24
    """
    text = normalize_korean_text(answer)

    if "-24" in text:
        return 1.0, "올바른 계산 결과 -24를 제시했습니다."

    wrong_patterns = [
        r"-32", r"-36", r"32", r"36", r"-28"
    ]
    if contains_any(text, wrong_patterns):
        return 0.0, "계산 결과가 올바르지 않습니다."

    return 0.0, "올바른 계산 결과 -24가 명확하지 않습니다."


def grade_q2_2_reason(answer: str):
    """
    2-(2) 이유 설명: 곱셈을 뺄셈보다 먼저 해야 함
    """
    text = normalize_korean_text(answer)

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
        return 0.0, "계산 순서에 대한 오개념이 있습니다."

    if has_multiplication and has_first:
        return 1.0, "곱셈을 먼저 해야 한다는 이유를 설명했습니다."

    return 0.0, "곱셈을 뺄셈보다 먼저 해야 한다는 의미가 부족합니다."


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
    text = normalize_korean_text(answer)

    if "건우" in text:
        return 1.0, "옳은 사람으로 건우를 선택했습니다."
    return 0.0, "옳은 사람 판단이 명확하지 않거나 틀렸습니다."


def grade_q3_power_sign(answer: str):
    """
    이유 설명: -2^4 = -16 이므로 음수
    (-2)^4 = 16으로 해석한 답안은 오답 처리
    """
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
    음수 2개를 곱하므로 양수
    """
    text = normalize_korean_text(answer)

    has_two_negatives = contains_any(text, [
        r"음수2개",
        r"음수가2개",
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

    if wrong_direction and not has_positive:
        return 0.0, "곱의 부호 판단 방향이 틀렸습니다."

    if has_two_negatives and has_positive:
        return 1.0, "음수 2개를 곱하므로 양수라는 설명이 있습니다."

    return 0.0, "음수 2개를 곱하면 양수라는 결론이 명확하지 않습니다."


def grade_q3(answer: str):
    scores = {}
    feedback = {}

    s, f = grade_q3_person(answer)
    scores["3 옳은 사람 판단"] = s
    feedback["3 옳은 사람 판단"] = f

    s, f = grade_q3_power_sign(answer)
    scores["3 -2^4 부호 판단"] = s
    feedback["3 -2^4 부호 판단"] = f

    s, f = grade_q3_product_sign(answer)
    scores["3 곱의 부호 설명"] = s
    feedback["3 곱의 부호 설명"] = f

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


제목
설명
완료된 문제 수 / 진행바
처음부터 버튼

[문제 1] [문제 2] [문제 3] [문제 4] [복습할 내용]

선택한 문제만 화면에 표시
답안 작성 칸 표시

맨 아래 전체 채점하기 버튼
