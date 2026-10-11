import math
import random
import time

import pygame


class MimiFace:
    """
    Mimi Bot Cute Animated Face

    هذا الملف مسؤول عن الشاشة فقط.
    لا يشغّل أي صوت.

    Expressions:
        idle
        happy
        giggle
        excited
        listening
        thinking
        talking
        wink
        love
        proud
        oops
        sad
        surprised
        sleepy
        spin_happy
        alert
        dizzy
    """

    EXPRESSIONS = {
        "idle",
        "happy",
        "giggle",
        "excited",
        "listening",
        "thinking",
        "talking",
        "wink",
        "love",
        "proud",
        "oops",
        "sad",
        "surprised",
        "sleepy",
        "spin_happy",
        "alert",
        "dizzy",
    }

    def __init__(
        self,
        fullscreen=True,
        width=1024,
        height=600,
        fps=60,
    ):

        # مهم: نشغّل فقط أجزاء Pygame الخاصة بالشاشة والخطوط.
        # لا نستخدم pygame.init() لأنه يهيّئ الـ mixer أيضًا
        # وقد يحجز جهاز الصوت ويمنع VoiceModule من الكلام على Raspberry Pi.
        pygame.display.init()
        pygame.font.init()

        # للتأكد أن Pygame لا يمسك جهاز الصوت نهائيًا.
        try:
            pygame.mixer.quit()
        except Exception:
            pass

        self.fullscreen = fullscreen
        self.width = width
        self.height = height
        self.fps = fps

        if fullscreen:

            self.screen = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN,
            )

            self.width, self.height = (
                self.screen.get_size()
            )

        else:

            self.screen = pygame.display.set_mode(
                (
                    width,
                    height,
                )
            )

        pygame.display.set_caption(
            "Mimi Bot"
        )

        self.clock = pygame.time.Clock()

        # =====================================================
        # COLORS
        # =====================================================

        self.background = (
            255,
            239,
            235,
        )

        self.eye_outline = (
            93,
            70,
            109,
        )

        self.eye_white = (
            255,
            255,
            255,
        )

        self.iris = (
            119,
            88,
            137,
        )

        self.pupil = (
            48,
            39,
            61,
        )

        self.highlight = (
            255,
            255,
            255,
        )

        self.cheek = (
            255,
            168,
            181,
        )

        self.cheek_light = (
            255,
            196,
            202,
        )

        self.mouth = (
            117,
            72,
            90,
        )

        self.mouth_inner = (
            91,
            53,
            69,
        )

        self.tongue = (
            255,
            139,
            158,
        )

        self.tooth = (
            255,
            255,
            255,
        )

        self.heart = (
            255,
            111,
            146,
        )

        self.star = (
            255,
            210,
            87,
        )

        self.tear = (
            114,
            195,
            255,
        )

        self.alert = (
            255,
            84,
            105,
        )

        # =====================================================
        # STATE
        # =====================================================

        self.expression = "idle"
        self.running = True

        self.start_time = (
            time.monotonic()
        )

        self.float_phase = 0.0
        self.talk_phase = 0.0
        self.spin_phase = 0.0
        self.effect_phase = 0.0
        self.dizzy_phase = 0.0

        # Blink
        self.is_blinking = False
        self.blink_amount = 0.0
        self.blink_start = 0.0

        self.last_blink = (
            time.monotonic()
        )

        self.next_blink = (
            random.uniform(
                2.5,
                5.5,
            )
        )

    # =========================================================
    # HELPERS
    # =========================================================

    def clamp(
        self,
        value,
        minimum,
        maximum,
    ):

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    # =========================================================
    # SET EXPRESSION
    # =========================================================

    def set_expression(
        self,
        expression,
    ):

        expression = str(
            expression
        ).strip().lower()

        if expression not in self.EXPRESSIONS:

            print(
                "⚠️ Unknown expression:",
                expression,
            )

            return False

        if expression != self.expression:

            print(
                f"🎀 Mimi face: "
                f"{self.expression} "
                f"-> {expression}"
            )

            # Start every expression from a clean animation phase.
            # In particular TALKING starts moving immediately instead of
            # inheriting an old mouth frame from a previous speech.
            self.start_time = time.monotonic()
            self.talk_phase = 0.0
            self.spin_phase = 0.0
            self.effect_phase = 0.0
            self.dizzy_phase = 0.0

        self.expression = expression

        return True

    # =========================================================
    # BACKGROUND
    # =========================================================

    def draw_background(self):

        self.screen.fill(
            self.background
        )

        glow = pygame.Surface(
            (
                self.width,
                self.height,
            ),
            pygame.SRCALPHA,
        )

        t = time.monotonic()

        circles = [
            (
                0.12,
                0.18,
                0.16,
            ),
            (
                0.88,
                0.20,
                0.14,
            ),
            (
                0.15,
                0.80,
                0.12,
            ),
            (
                0.86,
                0.78,
                0.16,
            ),
        ]

        for (
            rx,
            ry,
            rr,
        ) in circles:

            x = int(
                self.width * rx
                +
                math.sin(
                    t * 0.5 + rx
                )
                *
                10
            )

            y = int(
                self.height * ry
                +
                math.cos(
                    t * 0.45 + ry
                )
                *
                8
            )

            radius = int(
                min(
                    self.width,
                    self.height,
                )
                *
                rr
            )

            pygame.draw.circle(
                glow,
                (
                    255,
                    192,
                    210,
                    20,
                ),
                (
                    x,
                    y,
                ),
                radius,
            )

        self.screen.blit(
            glow,
            (
                0,
                0,
            ),
        )

    # =========================================================
    # BLINK
    # =========================================================

    def update_blink(self):

        if self.expression in {
            "happy",
            "giggle",
            "proud",
            "spin_happy",
            "sleepy",
            "wink",
            "dizzy",
        }:

            self.blink_amount = 0.0

            return

        now = time.monotonic()

        if (
            not self.is_blinking
            and
            now - self.last_blink
            >=
            self.next_blink
        ):

            self.is_blinking = True
            self.blink_start = now

        if not self.is_blinking:

            self.blink_amount = 0.0
            return

        elapsed = (
            now
            -
            self.blink_start
        )

        duration = 0.18

        progress = (
            elapsed
            /
            duration
        )

        if progress >= 1.0:

            self.is_blinking = False
            self.blink_amount = 0.0

            self.last_blink = now

            self.next_blink = (
                random.uniform(
                    2.6,
                    5.4,
                )
            )

        elif progress < 0.5:

            self.blink_amount = (
                progress * 2
            )

        else:

            self.blink_amount = (
                2
                -
                progress * 2
            )

    # =========================================================
    # FACE CENTER
    # =========================================================

    def get_face_center(self):

        self.float_phase += 0.025

        y = int(
            math.sin(
                self.float_phase
            )
            *
            self.height
            *
            0.006
        )

        return (
            self.width // 2,
            self.height // 2 + y,
        )

    # =========================================================
    # EYE GEOMETRY
    # =========================================================

    def eye_geometry(
        self,
        cx,
        cy,
    ):

        distance = int(
            self.width * 0.19
        )

        eye_y = (
            cy
            -
            int(
                self.height * 0.12
            )
        )

        eye_width = int(
            self.width * 0.16
        )

        eye_height = int(
            self.height * 0.30
        )

        return (
            eye_y,
            distance,
            eye_width,
            eye_height,
        )

    # =========================================================
    # OPEN EYE
    # =========================================================

    def draw_open_eye(
        self,
        x,
        y,
        width,
        height,
        look_x=0,
        look_y=0,
        scale=1.0,
    ):

        width = int(
            width * scale
        )

        height = int(
            height * scale
        )

        blink_scale = max(
            0.05,
            1.0
            -
            self.blink_amount,
        )

        current_height = max(
            7,
            int(
                height
                *
                blink_scale
            ),
        )

        eye_rect = pygame.Rect(
            x - width // 2,
            y - current_height // 2,
            width,
            current_height,
        )

        shadow_rect = eye_rect.move(
            0,
            int(
                self.height * 0.008
            ),
        )

        pygame.draw.ellipse(
            self.screen,
            (
                225,
                177,
                190,
            ),
            shadow_rect,
        )

        pygame.draw.ellipse(
            self.screen,
            self.eye_white,
            eye_rect,
        )

        pygame.draw.ellipse(
            self.screen,
            self.eye_outline,
            eye_rect,
            max(
                4,
                int(
                    self.height * 0.009
                ),
            ),
        )

        if current_height < 35:

            return

        iris_radius = int(
            min(
                width,
                current_height,
            )
            *
            0.32
        )

        max_x = int(
            width * 0.12
        )

        max_y = int(
            current_height * 0.09
        )

        look_x = self.clamp(
            look_x,
            -max_x,
            max_x,
        )

        look_y = self.clamp(
            look_y,
            -max_y,
            max_y,
        )

        px = int(
            x + look_x
        )

        py = int(
            y + look_y
        )

        pygame.draw.circle(
            self.screen,
            self.iris,
            (
                px,
                py,
            ),
            iris_radius,
        )

        pygame.draw.circle(
            self.screen,
            (
                101,
                72,
                122,
            ),
            (
                px,
                py,
            ),
            int(
                iris_radius * 0.77
            ),
        )

        pygame.draw.circle(
            self.screen,
            self.pupil,
            (
                px,
                py,
            ),
            int(
                iris_radius * 0.58
            ),
        )

        pygame.draw.circle(
            self.screen,
            self.highlight,
            (
                px
                -
                int(
                    iris_radius * 0.34
                ),
                py
                -
                int(
                    iris_radius * 0.36
                ),
            ),
            max(
                5,
                int(
                    iris_radius * 0.25
                ),
            ),
        )

        pygame.draw.circle(
            self.screen,
            self.highlight,
            (
                px
                +
                int(
                    iris_radius * 0.27
                ),
                py
                +
                int(
                    iris_radius * 0.20
                ),
            ),
            max(
                3,
                int(
                    iris_radius * 0.11
                ),
            ),
        )

    # =========================================================
    # HAPPY EYE
    # =========================================================

    def draw_happy_eye(
        self,
        x,
        y,
        width,
    ):

        height = int(
            self.height * 0.14
        )

        rect = pygame.Rect(
            x - width // 2,
            y - height // 2,
            width,
            height,
        )

        pygame.draw.arc(
            self.screen,
            self.eye_outline,
            rect,
            math.pi,
            2 * math.pi,
            max(
                8,
                int(
                    self.height * 0.018
                ),
            ),
        )

    # =========================================================
    # SLEEPY EYE
    # =========================================================

    def draw_sleepy_eye(
        self,
        x,
        y,
        width,
    ):

        rect = pygame.Rect(
            x - width // 2,
            y - 30,
            width,
            60,
        )

        pygame.draw.arc(
            self.screen,
            self.eye_outline,
            rect,
            0,
            math.pi,
            max(
                7,
                int(
                    self.height * 0.015
                ),
            ),
        )

    # =========================================================
    # DIZZY EYE
    # =========================================================

    def draw_dizzy_eye(
        self,
        x,
        y,
        size,
        phase,
    ):

        points = []

        turns = 3.2
        total_points = 55

        for index in range(
            total_points
        ):

            progress = (
                index
                /
                max(
                    1,
                    total_points - 1,
                )
            )

            angle = (
                progress
                *
                math.pi
                *
                2
                *
                turns
                +
                phase
            )

            radius = (
                progress
                *
                size
                *
                0.48
            )

            px = (
                x
                +
                math.cos(angle)
                *
                radius
            )

            py = (
                y
                +
                math.sin(angle)
                *
                radius
            )

            points.append(
                (
                    int(px),
                    int(py),
                )
            )

        if len(points) > 1:

            pygame.draw.lines(
                self.screen,
                self.eye_outline,
                False,
                points,
                max(
                    5,
                    int(
                        self.height * 0.012
                    ),
                ),
            )

    # =========================================================
    # CHEEKS
    # =========================================================

    def draw_cheeks(
        self,
        cx,
        cy,
        strong=False,
        bigger=False,
    ):

        distance = int(
            self.width * 0.255
        )

        y = (
            cy
            +
            int(
                self.height * 0.08
            )
        )

        width = int(
            self.width
            *
            (
                0.095
                if bigger
                else
                0.075
            )
        )

        height = int(
            self.height
            *
            (
                0.07
                if bigger
                else
                0.055
            )
        )

        color = (
            self.cheek
            if strong
            else
            self.cheek_light
        )

        for side in (
            -1,
            1,
        ):

            x = (
                cx
                +
                side * distance
            )

            pygame.draw.ellipse(
                self.screen,
                color,
                (
                    x - width // 2,
                    y - height // 2,
                    width,
                    height,
                ),
            )

            pygame.draw.ellipse(
                self.screen,
                (
                    255,
                    216,
                    222,
                ),
                (
                    x - width // 5,
                    y - height // 4,
                    width // 3,
                    height // 4,
                ),
            )

    # =========================================================
    # SMALL SMILE
    # =========================================================

    def draw_small_smile(
        self,
        cx,
        cy,
        width_factor=0.11,
    ):

        width = int(
            self.width
            *
            width_factor
        )

        height = int(
            self.height * 0.10
        )

        rect = pygame.Rect(
            cx - width // 2,
            cy - height // 2,
            width,
            height,
        )

        pygame.draw.arc(
            self.screen,
            self.mouth,
            rect,
            0,
            math.pi,
            max(
                7,
                int(
                    self.height * 0.015
                ),
            ),
        )

    # =========================================================
    # OPEN SMILE
    # =========================================================

    def draw_cute_open_smile(
        self,
        cx,
        cy,
        big=False,
        tongue=True,
    ):

        width_factor = (
            0.19
            if big
            else
            0.14
        )

        height_factor = (
            0.16
            if big
            else
            0.12
        )

        width = int(
            self.width
            *
            width_factor
        )

        height = int(
            self.height
            *
            height_factor
        )

        rect = pygame.Rect(
            cx - width // 2,
            cy - height // 2,
            width,
            height,
        )

        pygame.draw.ellipse(
            self.screen,
            self.mouth_inner,
            rect,
        )

        tooth_width = int(
            width * 0.62
        )

        tooth_height = int(
            height * 0.18
        )

        pygame.draw.ellipse(
            self.screen,
            self.tooth,
            (
                cx - tooth_width // 2,
                cy - height // 2 + 4,
                tooth_width,
                tooth_height,
            ),
        )

        if tongue:

            tongue_width = int(
                width * 0.58
            )

            tongue_height = int(
                height * 0.30
            )

            pygame.draw.ellipse(
                self.screen,
                self.tongue,
                (
                    cx
                    -
                    tongue_width // 2,
                    cy
                    +
                    int(
                        height * 0.17
                    ),
                    tongue_width,
                    tongue_height,
                ),
            )

    # =========================================================
    # TALKING MOUTH
    # =========================================================

    def draw_talking_mouth(
        self,
        cx,
        cy,
    ):

        self.talk_phase += 0.18

        frame = int(
            (
                math.sin(
                    self.talk_phase
                )
                +
                1
            )
            *
            1.5
        )

        frame = int(
            self.clamp(
                frame,
                0,
                3,
            )
        )

        if frame == 0:

            self.draw_small_smile(
                cx,
                cy,
                width_factor=0.09,
            )

        elif frame == 1:

            width = int(
                self.width * 0.075
            )

            height = int(
                self.height * 0.07
            )

            pygame.draw.ellipse(
                self.screen,
                self.mouth_inner,
                (
                    cx - width // 2,
                    cy - height // 2,
                    width,
                    height,
                ),
            )

        elif frame == 2:

            self.draw_cute_open_smile(
                cx,
                cy,
                big=False,
                tongue=False,
            )

        else:

            width = int(
                self.width * 0.10
            )

            height = int(
                self.height * 0.12
            )

            pygame.draw.ellipse(
                self.screen,
                self.mouth_inner,
                (
                    cx - width // 2,
                    cy - height // 2,
                    width,
                    height,
                ),
            )

    # =========================================================
    # HEART
    # =========================================================

    def draw_heart(
        self,
        x,
        y,
        size,
        color=None,
    ):

        if color is None:

            color = self.heart

        radius = max(
            2,
            size // 4,
        )

        pygame.draw.circle(
            self.screen,
            color,
            (
                x - radius,
                y - radius,
            ),
            radius,
        )

        pygame.draw.circle(
            self.screen,
            color,
            (
                x + radius,
                y - radius,
            ),
            radius,
        )

        pygame.draw.polygon(
            self.screen,
            color,
            [
                (
                    x - size // 2,
                    y - radius,
                ),
                (
                    x + size // 2,
                    y - radius,
                ),
                (
                    x,
                    y + size // 2,
                ),
            ],
        )

    # =========================================================
    # STAR
    # =========================================================

    def draw_star(
        self,
        x,
        y,
        radius,
        color=None,
    ):

        if color is None:

            color = self.star

        points = []

        for i in range(10):

            angle = (
                -math.pi / 2
                +
                i
                *
                math.pi / 5
            )

            r = (
                radius
                if i % 2 == 0
                else
                radius * 0.45
            )

            points.append(
                (
                    x
                    +
                    math.cos(angle)
                    *
                    r,
                    y
                    +
                    math.sin(angle)
                    *
                    r,
                )
            )

        pygame.draw.polygon(
            self.screen,
            color,
            points,
        )

    # =========================================================
    # EFFECT: FLOATING HEARTS
    # =========================================================

    def draw_floating_hearts(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        for index in range(5):

            phase = (
                t * 0.8
                +
                index * 1.4
            )

            rise = (
                phase % 4.0
            ) / 4.0

            side = (
                -1
                if index % 2 == 0
                else
                1
            )

            x = int(
                cx
                +
                side
                *
                (
                    self.width * 0.28
                    +
                    math.sin(
                        phase * 2
                    )
                    *
                    18
                )
            )

            y = int(
                cy
                +
                self.height * 0.23
                -
                rise
                *
                self.height
                *
                0.55
            )

            size = int(
                self.height
                *
                (
                    0.035
                    +
                    0.018
                    *
                    (
                        1 - rise
                    )
                )
            )

            self.draw_heart(
                x,
                y,
                size,
            )

    # =========================================================
    # EFFECT: EXCITED STARS
    # =========================================================

    def draw_excited_stars(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        for index in range(7):

            angle = (
                index
                *
                (
                    2 * math.pi / 7
                )
                +
                math.sin(
                    t * 1.2
                )
                *
                0.15
            )

            distance_x = (
                self.width * 0.34
            )

            distance_y = (
                self.height * 0.30
            )

            pulse = (
                1
                +
                0.15
                *
                math.sin(
                    t * 4
                    +
                    index
                )
            )

            x = int(
                cx
                +
                math.cos(angle)
                *
                distance_x
            )

            y = int(
                cy
                +
                math.sin(angle)
                *
                distance_y
            )

            radius = int(
                self.height
                *
                0.03
                *
                pulse
            )

            self.draw_star(
                x,
                y,
                radius,
            )

    # =========================================================
    # EFFECT: THINKING BUBBLES
    # =========================================================

    def draw_thinking_bubbles(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        for i in range(3):

            pulse = (
                1
                +
                0.15
                *
                math.sin(
                    t * 3
                    +
                    i
                )
            )

            radius = int(
                self.height
                *
                (
                    0.014
                    +
                    i * 0.008
                )
                *
                pulse
            )

            pygame.draw.circle(
                self.screen,
                self.eye_white,
                (
                    cx
                    +
                    int(
                        self.width
                        *
                        (
                            0.23
                            +
                            i * 0.038
                        )
                    ),
                    cy
                    -
                    int(
                        self.height
                        *
                        (
                            0.20
                            +
                            i * 0.055
                        )
                    ),
                ),
                radius,
            )

    # =========================================================
    # EFFECT: LISTENING WAVES
    # =========================================================

    def draw_listening_waves(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        base_x = (
            cx
            +
            int(
                self.width * 0.32
            )
        )

        base_y = (
            cy
            -
            int(
                self.height * 0.12
            )
        )

        for i in range(3):

            pulse = (
                1
                +
                0.10
                *
                math.sin(
                    t * 5
                    +
                    i
                )
            )

            radius = int(
                self.height
                *
                (
                    0.03
                    +
                    i * 0.025
                )
                *
                pulse
            )

            pygame.draw.arc(
                self.screen,
                self.eye_outline,
                (
                    base_x - radius,
                    base_y - radius,
                    radius * 2,
                    radius * 2,
                ),
                -0.9,
                0.9,
                max(
                    3,
                    int(
                        self.height * 0.007
                    ),
                ),
            )

    # =========================================================
    # EFFECT: SLEEP ZZZ
    # =========================================================

    def draw_sleep_effect(
        self,
        cx,
        cy,
    ):

        font = pygame.font.SysFont(
            None,
            max(
                38,
                int(
                    self.height * 0.075
                ),
            ),
            bold=True,
        )

        t = time.monotonic()

        for i in range(3):

            rise = (
                (
                    t * 0.35
                    +
                    i * 0.33
                )
                % 1.0
            )

            size_factor = (
                0.65
                +
                rise * 0.45
            )

            text = font.render(
                "Z",
                True,
                self.eye_outline,
            )

            text = pygame.transform.smoothscale(
                text,
                (
                    max(
                        1,
                        int(
                            text.get_width()
                            *
                            size_factor
                        ),
                    ),
                    max(
                        1,
                        int(
                            text.get_height()
                            *
                            size_factor
                        ),
                    ),
                ),
            )

            self.screen.blit(
                text,
                (
                    cx
                    +
                    int(
                        self.width
                        *
                        (
                            0.23
                            +
                            i * 0.035
                        )
                    ),
                    cy
                    -
                    int(
                        self.height
                        *
                        (
                            0.16
                            +
                            rise * 0.30
                        )
                    ),
                ),
            )

    # =========================================================
    # EFFECT: SAD TEAR
    # =========================================================

    def draw_sad_tear(
        self,
        x,
        eye_y,
    ):

        t = time.monotonic()

        fall = (
            t * 0.45
        ) % 1.0

        tear_y = int(
            eye_y
            +
            self.height * 0.10
            +
            fall
            *
            self.height
            *
            0.14
        )

        width = int(
            self.width * 0.016
        )

        height = int(
            self.height * 0.045
        )

        pygame.draw.ellipse(
            self.screen,
            self.tear,
            (
                x,
                tear_y,
                width,
                height,
            ),
        )

    # =========================================================
    # EFFECT: OOPS QUESTION
    # =========================================================

    def draw_oops_effect(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        wobble = int(
            math.sin(
                t * 6
            )
            *
            10
        )

        font = pygame.font.SysFont(
            None,
            max(
                55,
                int(
                    self.height * 0.10
                ),
            ),
            bold=True,
        )

        text = font.render(
            "?",
            True,
            self.eye_outline,
        )

        self.screen.blit(
            text,
            (
                cx
                +
                int(
                    self.width * 0.29
                )
                +
                wobble,
                cy
                -
                int(
                    self.height * 0.31
                ),
            ),
        )

    # =========================================================
    # EFFECT: SURPRISE RINGS
    # =========================================================

    def draw_surprise_effect(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        pulse = (
            t * 1.8
        ) % 1.0

        radius = int(
            min(
                self.width,
                self.height,
            )
            *
            (
                0.34
                +
                pulse * 0.10
            )
        )

        thickness = max(
            2,
            int(
                7
                *
                (
                    1 - pulse
                )
            ),
        )

        pygame.draw.circle(
            self.screen,
            (
                255,
                206,
                117,
            ),
            (
                cx,
                cy,
            ),
            radius,
            thickness,
        )

    # =========================================================
    # EFFECT: ALERT
    # =========================================================

    def draw_alert_effect(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        pulse = (
            math.sin(
                t * 6
            )
            +
            1
        ) / 2

        border = int(
            8
            +
            pulse * 10
        )

        pygame.draw.rect(
            self.screen,
            self.alert,
            (
                border // 2,
                border // 2,
                self.width - border,
                self.height - border,
            ),
            border,
            border_radius=35,
        )

        # Soft red flash
        flash_alpha = int(
            18
            +
            pulse * 25
        )

        overlay = pygame.Surface(
            (
                self.width,
                self.height,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                255,
                60,
                80,
                flash_alpha,
            )
        )

        self.screen.blit(
            overlay,
            (
                0,
                0,
            ),
        )

        # !
        font = pygame.font.SysFont(
            None,
            max(
                70,
                int(
                    self.height * 0.14
                ),
            ),
            bold=True,
        )

        text = font.render(
            "!",
            True,
            self.alert,
        )

        scale = (
            1
            +
            pulse * 0.10
        )

        text = pygame.transform.smoothscale(
            text,
            (
                int(
                    text.get_width()
                    *
                    scale
                ),
                int(
                    text.get_height()
                    *
                    scale
                ),
            ),
        )

        self.screen.blit(
            text,
            (
                cx
                -
                text.get_width() // 2,
                int(
                    self.height * 0.05
                ),
            ),
        )

    # =========================================================
    # EFFECT: DIZZY STARS
    # =========================================================

    def draw_dizzy_effect(
        self,
        cx,
        cy,
    ):

        t = time.monotonic()

        for index in range(6):

            angle = (
                t * 2.5
                +
                index
                *
                (
                    2 * math.pi / 6
                )
            )

            x = int(
                cx
                +
                math.cos(angle)
                *
                self.width
                *
                0.31
            )

            y = int(
                cy
                -
                self.height * 0.20
                +
                math.sin(angle)
                *
                self.height
                *
                0.13
            )

            radius = int(
                self.height
                *
                (
                    0.028
                    +
                    0.009
                    *
                    (
                        1
                        +
                        math.sin(
                            angle * 2
                        )
                    )
                )
            )

            self.draw_star(
                x,
                y,
                radius,
            )

    # =========================================================
    # IDLE
    # =========================================================

    def draw_idle(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        t = time.monotonic()

        look_x = int(
            math.sin(
                t * 0.45
            )
            *
            self.width
            *
            0.006
        )

        look_y = int(
            math.cos(
                t * 0.33
            )
            *
            self.height
            *
            0.004
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            look_x,
            look_y,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            look_x,
            look_y,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        self.draw_small_smile(
            cx,
            cy
            +
            int(
                self.height * 0.19
            ),
        )

    # =========================================================
    # HAPPY
    # =========================================================

    def draw_happy(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            _,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_happy_eye(
            cx - distance,
            eye_y,
            width,
        )

        self.draw_happy_eye(
            cx + distance,
            eye_y,
            width,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
            bigger=True,
        )

        self.draw_cute_open_smile(
            cx,
            cy
            +
            int(
                self.height * 0.20
            ),
            big=True,
        )

    # =========================================================
    # GIGGLE
    # =========================================================

    def draw_giggle(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            _,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        bounce = int(
            math.sin(
                time.monotonic() * 7
            )
            *
            4
        )

        self.draw_happy_eye(
            cx - distance,
            eye_y + bounce,
            width,
        )

        self.draw_happy_eye(
            cx + distance,
            eye_y + bounce,
            width,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
            bigger=True,
        )

        self.draw_cute_open_smile(
            cx,
            cy
            +
            int(
                self.height * 0.20
            )
            +
            bounce,
        )

        self.draw_floating_hearts(
            cx,
            cy,
        )

    # =========================================================
    # EXCITED
    # =========================================================

    def draw_excited(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            scale=1.12,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            scale=1.12,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
            bigger=True,
        )

        self.draw_cute_open_smile(
            cx,
            cy
            +
            int(
                self.height * 0.21
            ),
            big=True,
        )

        self.draw_excited_stars(
            cx,
            cy,
        )

    # =========================================================
    # LISTENING
    # =========================================================

    def draw_listening(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            scale=1.06,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            scale=1.06,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        pygame.draw.circle(
            self.screen,
            self.mouth_inner,
            (
                cx,
                cy
                +
                int(
                    self.height * 0.19
                ),
            ),
            max(
                8,
                int(
                    self.height * 0.018
                ),
            ),
        )

        self.draw_listening_waves(
            cx,
            cy,
        )

    # =========================================================
    # THINKING
    # =========================================================

    def draw_thinking(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        t = time.monotonic()

        look_x = int(
            math.sin(
                t
            )
            *
            self.width
            *
            0.008
        )

        look_y = -int(
            self.height * 0.022
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            look_x,
            look_y,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            look_x,
            look_y,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        pygame.draw.line(
            self.screen,
            self.mouth,
            (
                cx
                -
                int(
                    self.width * 0.035
                ),
                cy
                +
                int(
                    self.height * 0.20
                ),
            ),
            (
                cx
                +
                int(
                    self.width * 0.035
                ),
                cy
                +
                int(
                    self.height * 0.20
                ),
            ),
            8,
        )

        self.draw_thinking_bubbles(
            cx,
            cy,
        )

    # =========================================================
    # TALKING
    # =========================================================

    def draw_talking(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
        )

        self.draw_talking_mouth(
            cx,
            cy
            +
            int(
                self.height * 0.19
            ),
        )

    # =========================================================
    # WINK
    # =========================================================

    def draw_wink(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_happy_eye(
            cx - distance,
            eye_y,
            width,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
        )

        self.draw_small_smile(
            cx,
            cy
            +
            int(
                self.height * 0.20
            ),
            width_factor=0.16,
        )

        self.draw_star(
            cx
            -
            int(
                self.width * 0.30
            ),
            cy
            -
            int(
                self.height * 0.23
            ),
            int(
                self.height * 0.045
            ),
        )

    # =========================================================
    # LOVE
    # =========================================================

    def draw_love(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
            bigger=True,
        )

        self.draw_small_smile(
            cx,
            cy
            +
            int(
                self.height * 0.20
            ),
            width_factor=0.16,
        )

        self.draw_floating_hearts(
            cx,
            cy,
        )

    # =========================================================
    # PROUD
    # =========================================================

    def draw_proud(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            _,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_happy_eye(
            cx - distance,
            eye_y,
            width,
        )

        self.draw_happy_eye(
            cx + distance,
            eye_y,
            width,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
        )

        self.draw_small_smile(
            cx,
            cy
            +
            int(
                self.height * 0.20
            ),
            width_factor=0.17,
        )

        self.draw_star(
            cx,
            cy
            -
            int(
                self.height * 0.34
            ),
            int(
                self.height * 0.05
            ),
        )

    # =========================================================
    # OOPS
    # =========================================================

    def draw_oops(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y + 6,
            width,
            int(
                height * 0.92
            ),
        )

        self.draw_open_eye(
            cx + distance,
            eye_y - 4,
            width,
            height,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
        )

        pygame.draw.line(
            self.screen,
            self.mouth,
            (
                cx
                -
                int(
                    self.width * 0.045
                ),
                cy
                +
                int(
                    self.height * 0.20
                ),
            ),
            (
                cx
                +
                int(
                    self.width * 0.045
                ),
                cy
                +
                int(
                    self.height * 0.18
                ),
            ),
            8,
        )

        self.draw_oops_effect(
            cx,
            cy,
        )

    # =========================================================
    # SAD
    # =========================================================

    def draw_sad(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        down = int(
            self.height * 0.015
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            0,
            down,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            0,
            down,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        mouth_width = int(
            self.width * 0.12
        )

        mouth_height = int(
            self.height * 0.09
        )

        rect = pygame.Rect(
            cx - mouth_width // 2,
            cy
            +
            int(
                self.height * 0.19
            ),
            mouth_width,
            mouth_height,
        )

        pygame.draw.arc(
            self.screen,
            self.mouth,
            rect,
            math.pi,
            2 * math.pi,
            8,
        )

        self.draw_sad_tear(
            cx
            +
            distance
            +
            int(
                width * 0.38
            ),
            eye_y,
        )

    # =========================================================
    # SURPRISED
    # =========================================================

    def draw_surprised(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            scale=1.12,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            scale=1.12,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        pygame.draw.ellipse(
            self.screen,
            self.mouth_inner,
            (
                cx
                -
                int(
                    self.width * 0.037
                ),
                cy
                +
                int(
                    self.height * 0.15
                ),
                int(
                    self.width * 0.074
                ),
                int(
                    self.height * 0.115
                ),
            ),
        )

        self.draw_surprise_effect(
            cx,
            cy,
        )

    # =========================================================
    # SLEEPY
    # =========================================================

    def draw_sleepy(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            _,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_sleepy_eye(
            cx - distance,
            eye_y,
            width,
        )

        self.draw_sleepy_eye(
            cx + distance,
            eye_y,
            width,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        pygame.draw.ellipse(
            self.screen,
            self.mouth_inner,
            (
                cx - 22,
                cy
                +
                int(
                    self.height * 0.18
                ),
                44,
                35,
            ),
        )

        self.draw_sleep_effect(
            cx,
            cy,
        )

    # =========================================================
    # SPIN HAPPY
    # =========================================================

    def draw_spin_happy(
        self,
        cx,
        cy,
    ):

        self.spin_phase += 0.12

        wiggle = int(
            math.sin(
                self.spin_phase
            )
            *
            self.width
            *
            0.008
        )

        cx += wiggle

        (
            eye_y,
            distance,
            width,
            _,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_happy_eye(
            cx - distance,
            eye_y,
            width,
        )

        self.draw_happy_eye(
            cx + distance,
            eye_y,
            width,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
            bigger=True,
        )

        self.draw_cute_open_smile(
            cx,
            cy
            +
            int(
                self.height * 0.20
            ),
            big=True,
        )

        t = time.monotonic()

        for i in range(6):

            angle = (
                t * 2
                +
                i
                *
                (
                    2 * math.pi / 6
                )
            )

            sx = int(
                cx
                +
                math.cos(angle)
                *
                self.width
                *
                0.34
            )

            sy = int(
                cy
                +
                math.sin(angle)
                *
                self.height
                *
                0.29
            )

            self.draw_star(
                sx,
                sy,
                int(
                    self.height * 0.035
                ),
            )

    # =========================================================
    # ALERT
    # =========================================================

    def draw_alert(
        self,
        cx,
        cy,
    ):

        (
            eye_y,
            distance,
            width,
            height,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        self.draw_open_eye(
            cx - distance,
            eye_y,
            width,
            height,
            scale=1.08,
        )

        self.draw_open_eye(
            cx + distance,
            eye_y,
            width,
            height,
            scale=1.08,
        )

        self.draw_cheeks(
            cx,
            cy,
        )

        pygame.draw.ellipse(
            self.screen,
            self.alert,
            (
                cx
                -
                int(
                    self.width * 0.035
                ),
                cy
                +
                int(
                    self.height * 0.16
                ),
                int(
                    self.width * 0.07
                ),
                int(
                    self.height * 0.10
                ),
            ),
        )

        self.draw_alert_effect(
            cx,
            cy,
        )

    # =========================================================
    # DIZZY
    # =========================================================

    def draw_dizzy(
        self,
        cx,
        cy,
    ):

        self.dizzy_phase += 0.08

        shake_x = int(
            math.sin(
                self.dizzy_phase * 4
            )
            *
            self.width
            *
            0.008
        )

        shake_y = int(
            math.cos(
                self.dizzy_phase * 3
            )
            *
            self.height
            *
            0.005
        )

        cx += shake_x
        cy += shake_y

        (
            eye_y,
            distance,
            width,
            _,
        ) = self.eye_geometry(
            cx,
            cy,
        )

        spiral_size = int(
            width * 0.90
        )

        self.draw_dizzy_eye(
            cx - distance,
            eye_y,
            spiral_size,
            self.dizzy_phase,
        )

        self.draw_dizzy_eye(
            cx + distance,
            eye_y,
            spiral_size,
            -self.dizzy_phase,
        )

        self.draw_cheeks(
            cx,
            cy,
            strong=True,
        )

        # Dizzy mouth
        mouth_y = (
            cy
            +
            int(
                self.height * 0.20
            )
        )

        points = [
            (
                cx
                -
                int(
                    self.width * 0.055
                ),
                mouth_y,
            ),
            (
                cx
                -
                int(
                    self.width * 0.018
                ),
                mouth_y - 8,
            ),
            (
                cx
                +
                int(
                    self.width * 0.018
                ),
                mouth_y + 8,
            ),
            (
                cx
                +
                int(
                    self.width * 0.055
                ),
                mouth_y,
            ),
        ]

        pygame.draw.lines(
            self.screen,
            self.mouth,
            False,
            points,
            8,
        )

        self.draw_dizzy_effect(
            cx,
            cy,
        )

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):

        self.update_blink()

        self.draw_background()

        (
            cx,
            cy,
        ) = self.get_face_center()

        if self.expression == "idle":

            self.draw_idle(
                cx,
                cy,
            )

        elif self.expression == "happy":

            self.draw_happy(
                cx,
                cy,
            )

        elif self.expression == "giggle":

            self.draw_giggle(
                cx,
                cy,
            )

        elif self.expression == "excited":

            self.draw_excited(
                cx,
                cy,
            )

        elif self.expression == "listening":

            self.draw_listening(
                cx,
                cy,
            )

        elif self.expression == "thinking":

            self.draw_thinking(
                cx,
                cy,
            )

        elif self.expression == "talking":

            self.draw_talking(
                cx,
                cy,
            )

        elif self.expression == "wink":

            self.draw_wink(
                cx,
                cy,
            )

        elif self.expression == "love":

            self.draw_love(
                cx,
                cy,
            )

        elif self.expression == "proud":

            self.draw_proud(
                cx,
                cy,
            )

        elif self.expression == "oops":

            self.draw_oops(
                cx,
                cy,
            )

        elif self.expression == "sad":

            self.draw_sad(
                cx,
                cy,
            )

        elif self.expression == "surprised":

            self.draw_surprised(
                cx,
                cy,
            )

        elif self.expression == "sleepy":

            self.draw_sleepy(
                cx,
                cy,
            )

        elif self.expression == "spin_happy":

            self.draw_spin_happy(
                cx,
                cy,
            )

        elif self.expression == "alert":

            self.draw_alert(
                cx,
                cy,
            )

        elif self.expression == "dizzy":

            self.draw_dizzy(
                cx,
                cy,
            )

        pygame.display.flip()

    # =========================================================
    # EVENTS
    # =========================================================

    def process_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                self.running = False

            elif event.type == pygame.KEYDOWN:

                if event.key in {
                    pygame.K_ESCAPE,
                    pygame.K_q,
                }:

                    self.running = False

                elif event.key == pygame.K_1:

                    self.set_expression(
                        "idle"
                    )

                elif event.key == pygame.K_2:

                    self.set_expression(
                        "happy"
                    )

                elif event.key == pygame.K_3:

                    self.set_expression(
                        "giggle"
                    )

                elif event.key == pygame.K_4:

                    self.set_expression(
                        "excited"
                    )

                elif event.key == pygame.K_5:

                    self.set_expression(
                        "listening"
                    )

                elif event.key == pygame.K_6:

                    self.set_expression(
                        "thinking"
                    )

                elif event.key == pygame.K_7:

                    self.set_expression(
                        "talking"
                    )

                elif event.key == pygame.K_8:

                    self.set_expression(
                        "wink"
                    )

                elif event.key == pygame.K_9:

                    self.set_expression(
                        "love"
                    )

                elif event.key == pygame.K_0:

                    self.set_expression(
                        "proud"
                    )

                elif event.key == pygame.K_o:

                    self.set_expression(
                        "oops"
                    )

                elif event.key == pygame.K_s:

                    self.set_expression(
                        "sad"
                    )

                elif event.key == pygame.K_u:

                    self.set_expression(
                        "surprised"
                    )

                elif event.key == pygame.K_z:

                    self.set_expression(
                        "sleepy"
                    )

                elif event.key == pygame.K_r:

                    self.set_expression(
                        "spin_happy"
                    )

                elif event.key == pygame.K_a:

                    self.set_expression(
                        "alert"
                    )

                elif event.key == pygame.K_d:

                    self.set_expression(
                        "dizzy"
                    )

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):

        if not self.running:

            return False

        self.process_events()

        self.draw()

        self.clock.tick(
            self.fps
        )

        return self.running

    # =========================================================
    # RUN
    # =========================================================

    def run(self):

        print()
        print("=" * 70)
        print("🎀 MIMI BOT - CUTE FACE + EFFECTS")
        print("=" * 70)

        print()
        print("1 = Idle")
        print("2 = Happy")
        print("3 = Giggle")
        print("4 = Excited ⭐")
        print("5 = Listening )))")
        print("6 = Thinking")
        print("7 = Talking")
        print("8 = Wink")
        print("9 = Love ❤️")
        print("0 = Proud")
        print()
        print("O = Oops ?")
        print("S = Sad 💧")
        print("U = Surprised")
        print("Z = Sleepy Zzz")
        print("R = Spin Happy ⭐")
        print("A = Alert 🚨")
        print("D = Dizzy 🌀")
        print()
        print("Q / ESC = Exit")
        print()

        while self.running:

            self.update()

        self.close()

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        self.running = False

        try:

            pygame.quit()

        except Exception:

            pass


# =============================================================
# TEST
# =============================================================

def main():

    face = MimiFace(
        fullscreen=True
    )

    face.run()


if __name__ == "__main__":

    main()