# Phase 7: Questions on an asset

**Module:** Catalogue (model `AssetQuestion`, services `ask_question`, `answer_question`, `withdraw_question`,
`questions_to_answer`) · **Migration:** `catalogue 0004_asset_questions` · **Screens:** the Q&A section in every
asset panel, and `/assets/questions/`. "Our assets" shows a notice when questions are waiting, and its menu badge
counts them.

## Who sees and does what

| Who | Can |
|---|---|
| Anyone who may **view** the asset (same `can_view` rule as the panel) | Read its questions and answers. They see the asker's **unit**, not their name. |
| The same people, except those who look after the item | **Ask** (3–500 characters, at most 3 unanswered per person per item), and **withdraw** their own unanswered question |
| The custodian, or `asset.register` / `asset.custody` for the unit | **Answer** (3–1,000 characters) and edit the answer. They see the asker's name and unit. |
| The asker | Sees "You asked", and every question they've asked on `/assets/questions/` |

## Design decisions

**Q1. Focused, not a chat.** Each question has one answer, which the custodian can edit. There are no threads and
no replies to answers.

**Q2. Privacy.** Questions are about the item, so everyone who can see the item can read them. That saves
repeating "does it have HDMI?". The asker's name is shown only to themselves and to the people who answer.
Everyone else sees "Asked by someone in ME". If someone loses sight of the item (for example, it is unpublished),
they can no longer ask about it.

**Q3. Notifications.** A new question notifies the custodian, in-app and by e-mail. An answer notifies the asker,
and so does a later edit to the answer. Both go through `Msg`, so they are stored in English and Arabic, and they
link to the asset panel.

**Q4. Unanswered questions.** The custodian's "Waiting for your answer" list is oldest first and flags questions
waiting **14 days or more**. Askers can withdraw an unanswered question. Answered questions stay up for others
to read.

**Q5. Archived items.** Retired, donated, recycled and disposed items take no new questions. An unanswered
question on a donated, recycled or disposed item shows as "Closed without an answer: the item has left the
register". It can't be answered and drops out of the custodian's list. Answered questions stay visible on the
kept record.

**Q6. Input.** Whitespace is collapsed and the length limits are checked on the server. Text is shown escaped,
in `dir="auto"` boxes so English and Arabic both read correctly. Asking and answering are recorded in the
audit log.

## Tests

`tests/test_questions.py` covers:
- ask and answer, with both notifications in two languages;
- validation for empty, too short and too long text;
- who may ask and answer;
- the spam guard;
- archived items;
- withdrawing;
- the unanswered count;
- name privacy in the panel;
- asking and answering through the panel;
- the questions page, including the waiting-14-days flag.
