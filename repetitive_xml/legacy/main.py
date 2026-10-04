# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#                notes
# ----------------------------------------------------------------------------------------
'''
Kutay Coskuner, 2025
This code is licensed under the MIT License. You can use, modify, and distribute it freely.
However, it is provided "as is," without any warranties or guarantees of any kind.
For details, visit: https://opensource.org/licenses/MIT

- description
    Generates a complete <cooldownentry> block from a YAML configuration.

    The generated cooldownentry contains:
        - cooldownentry attributes
        - one trigger for every second in the configured duration range
        - automatically calculated minutes and seconds
        - correct singular/plural wording

    The generated block is inserted into the <cooldowns> element
    of the input XML file.

- metadata
    Configuration:
        config.yaml

    Input:
        input/<filename>

    Output:
        output/<filename>

- install
    pip install -r requirements.txt

- sources
    https://pyyaml.org/
    https://docs.python.org/3/library/re.html

- todo
    - Add support for replacing an existing cooldownentry.
    - Add optional automatic backup of the input file.
    - Add support for multiple cooldownentries.
'''
# ----------------------------------------------------------------------------------------
#                libraries
# ----------------------------------------------------------------------------------------

import os

import yaml


# ----------------------------------------------------------------------------------------
#                variables
# ----------------------------------------------------------------------------------------

CONFIG_FILE = "config.yaml"

INPUT_DIR = "input"
OUTPUT_DIR = "output"


# ----------------------------------------------------------------------------------------
#                functions
# ----------------------------------------------------------------------------------------

def load_config(config_file):
    """
    Load the YAML configuration file.
    """

    with open(config_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def generate_trigger(duration, trigger_config):
    """
    Generate one trigger entry for the given duration.
    """

    minutes = duration // 60
    seconds = duration % 60

    time_parts = []

    if minutes > 0:
        minute_word = "m" if minutes == 1 else "m"
        time_parts.append(f"{minutes}{minute_word} ")

    if seconds > 0:
        second_word = "s" if seconds == 1 else "s"
        time_parts.append(f"{seconds}{second_word}")

    time_text = "".join(time_parts)

    trigger_text = trigger_config["text"].format(
        time=time_text,
        minutes=minutes,
        seconds=seconds,
    )

    trigger_type = trigger_config["type"]

    return (
        f'        <trigger triggertype="{trigger_type}" duration="{duration}"\n'
        f'            triggertext="{trigger_text}" />\n'
    )


def generate_triggers(start_duration, end_duration, trigger_config):
    """
    Generate all trigger entries in the configured duration range.
    """

    triggers = []

    for duration in range(start_duration, end_duration + 1):
        triggers.append(
            generate_trigger(
                duration,
                trigger_config,
            )
        )

    return "".join(triggers)


def generate_cooldown_block(cooldown_config):
    """
    Generate the complete cooldownentry block.
    """

    name = cooldown_config["name"]
    default_cooldown = cooldown_config["defaultcooldown"]
    cooldown_bar_type = cooldown_config["cooldownbartype"]
    hue = cooldown_config["hue"]
    hide_when_inactive = cooldown_config["hidewheninactive"]

    duration_config = cooldown_config["duration"]

    start_duration = duration_config["start"]
    end_duration = duration_config["end"]

    trigger_config = cooldown_config["trigger"]

    triggers = generate_triggers(
        start_duration,
        end_duration,
        trigger_config,
    )

    hide_when_inactive = str(hide_when_inactive).capitalize()

    block = (
        f'    <cooldownentry name="{name}" '
        f'defaultcooldown="{default_cooldown}" '
        f'cooldownbartype="{cooldown_bar_type}" '
        f'hue="{hue}"\n'
        f'        hidewheninactive="{hide_when_inactive}">\n\n'
        f'{triggers}'
        f'\n'
        f'    </cooldownentry>'
    )

    return block


def insert_cooldown_block(xml_content, cooldown_block):
    """
    Insert the generated cooldown block immediately before </cooldowns>.
    """

    closing_tag = "</cooldowns>"

    if closing_tag not in xml_content:
        raise ValueError(
            'Could not find the closing "</cooldowns>" tag.'
        )

    return xml_content.replace(
        closing_tag,
        f"{cooldown_block}\n\n{closing_tag}",
        1,
    )


# ----------------------------------------------------------------------------------------
#                main
# ----------------------------------------------------------------------------------------

def main():
    config = load_config(CONFIG_FILE)

    input_file = os.path.join(
        INPUT_DIR,
        config["input_file"],
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        config["output_file"],
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cooldown_config = config["cooldown"]

    print(f'Input: {input_file}')
    print(f'Cooldown: {cooldown_config["name"]}')

    with open(input_file, "r", encoding="utf-8") as file:
        xml_content = file.read()

    cooldown_block = generate_cooldown_block(
        cooldown_config,
    )

    updated_xml = insert_cooldown_block(
        xml_content,
        cooldown_block,
    )

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(updated_xml)

    start_duration = cooldown_config["duration"]["start"]
    end_duration = cooldown_config["duration"]["end"]

    print(
        f"Duration: {start_duration} - {end_duration} seconds"
    )

    print(f"Output: {output_file}")
    print("Done.")


# ----------------------------------------------------------------------------------------
#                start
# ----------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
