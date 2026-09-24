# Automation blueprints

LockLearn P4.9 ships three example Home Assistant automation blueprints under:

`blueprints/automation/locklearn/`

They are repository assets intended for explicit Home Assistant Blueprint import.
The custom integration does not silently copy files into a user's Home Assistant
configuration directory.

## Included blueprints

### Correct / wrong light feedback

File:

`correct_wrong_light_feedback.yaml`

Events:

- `locklearn_quiz_correct`
- `locklearn_quiz_wrong`

The automation flashes a selected light green or red. An optional
`profile_id` filter can restrict it to one LockLearn Profile.

### Daily goal reward

File:

`daily_goal_reward.yaml`

Event:

- `locklearn_daily_goal_reached`

The automation activates a selected Home Assistant scene when the daily goal is
reached. It can also be restricted to one Profile.

### Repeated failure encouragement

File:

`repeated_failure_encouragement.yaml`

Event:

- `locklearn_answered`

The automation fires once when `consecutive_wrong` reaches the configured
threshold exactly. It creates a content-free persistent notification and can
optionally call:

`locklearn.pause_track`

Because event-triggered automations do not carry a trusted LockLearn user
context, automatic Track pause requires the Profile setting
`allow_unattended_actions=true`. P4.8 still applies the unattended action
allowlist and durable audit.

## Import

In Home Assistant:

1. open **Settings → Automations & scenes → Blueprints**;
2. choose **Import Blueprint**;
3. paste the GitHub URL of the desired file under
   `blueprints/automation/locklearn/`;
4. import it, then create an automation from the imported blueprint.

The blueprint metadata contains a stable `source_url` pointing to the main
LockLearn repository path so Home Assistant can retain source provenance.

## Privacy and authority

The shipped blueprints intentionally depend only on the stable P4.8 public
surface:

- event names;
- `profile_id`;
- `track_id`;
- result/counter fields such as `consecutive_wrong`.

They do not access prompt text, answer text, translations, user responses,
LearningItem IDs or CardDefinition IDs.

The blueprints never treat an output event as write authority. The only
LockLearn state-changing call included by an example is the optional
`locklearn.pause_track` service, which re-enters the P4.8 authorization and
unattended-audit boundary.

## Validation

Repository tests load every shipped YAML file using Home Assistant's
`Blueprint` model with `AUTOMATION_BLUEPRINT_SCHEMA`, then verify:

- the exact expected blueprint set;
- stable source URLs;
- only documented LockLearn events/services are referenced;
- no private learning-content event fields are consumed.
