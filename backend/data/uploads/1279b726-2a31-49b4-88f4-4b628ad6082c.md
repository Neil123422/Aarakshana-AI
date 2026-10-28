# Demo Prompt — Indian Paralegal AI (BNS / BNSS / BSA)

## Test Query 1: Substantive Law (Bharatiya Nyaya Sanhita 2023)
"A person is accused of causing the death of another by a rash and negligent act. Under the Bharatiya Nyaya Sanhita, 2023, which section applies, what is the punishment, and how does this correspond to the old Section 304A of the IPC?"

Expected behavior:
- Retrieve BNS Section 106 (causing death by negligence).
- Cite exact verbatim text from the Bare Act.
- Note the transition: old IPC 304A → new BNS 106.
- Include legal disclaimer.

## Test Query 2: Criminal Procedure (Bharatiya Nagarik Suraksha Sanhita 2023)
"What is the procedure for arresting a woman after sunset under the BNSS, 2023? Cite the exact section and explain any conditions or safeguards."

Expected behavior:
- Retrieve BNSS Section 43 (arrest of woman after sunset — requires permission of a woman police officer).
- Show the cited section card.

## Test Query 3: Evidence (Bharatiya Sakshya Adhiniyam 2023)
"Explain the concept of 'presumption of fact' under the BSA 2023. Which section defines it, and what is the burden of proof?"

Expected behavior:
- Retrieve BSA Section 4 or related provisions on presumptions.
- Provide structured response with Act, Section, title, verbatim text, and transition notes.

---
Use this prompt to verify:
1. Keyword extraction from plain English.
2. SQLite FTS5 retrieval (top 5 sections across BNS / BNSS / BSA).
3. LLM injection with verbatim sections.
4. Citation of exact Act + Section numbers.
5. Old IPC/CrPC transition notes where relevant.
6. Legal disclaimer included in response.
