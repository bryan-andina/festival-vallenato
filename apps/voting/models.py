"""
Domain models for the Vallenato Legend Festival voting system.
Adheres to Clean Architecture, SOLID principles, and Django best practices.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.common.models import TimeStampedModel

User = get_user_model()


class Edition(TimeStampedModel):
    """
    Represents an annual edition of the Vallenato Legend Festival.
    """
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Edition Name",
        help_text="Official name of the festival edition (e.g., '60° Festival de la Leyenda Vallenata 2027')."
    )
    year = models.PositiveSmallIntegerField(
        unique=True,
        verbose_name="Festival Year",
        help_text="Calendar year of the festival edition."
    )
    slogan = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Slogan / Tribute",
        help_text="Special dedication, tribute or theme of this edition."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="General description and context of the annual edition."
    )
    start_date = models.DateField(
        verbose_name="Start Date",
        help_text="Official opening date of the festival."
    )
    end_date = models.DateField(
        verbose_name="End Date",
        help_text="Official closing date of the festival."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active?",
        help_text="Designates whether this edition is currently open or visible to the public."
    )

    class Meta:
        db_table = "festival_edition"
        verbose_name = "Festival Edition"
        verbose_name_plural = "Festival Editions"
        ordering = ["-year"]

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                "end_date": "The festival end date cannot be earlier than the start date."
            })


class Category(TimeStampedModel):
    """
    Represents an official musical or cultural contest category within a festival edition.
    Examples: Acordeón Profesional, Canción Vallenata Inédita, Piqueria Mayor, etc.
    """
    edition = models.ForeignKey(
        Edition,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="Festival Edition"
    )
    name = models.CharField(
        max_length=120,
        verbose_name="Category Name",
        help_text="Name of the contest category (e.g., 'Acordeón Profesional')."
    )
    code = models.SlugField(
        max_length=60,
        blank=True,
        verbose_name="Category Code / Slug",
        help_text="URL-friendly identifier for the category."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Category Description",
        help_text="Rules, judging guidelines, and eligibility for this contest category."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active?",
        help_text="Designates whether this category is currently active for voting/display."
    )

    class Meta:
        db_table = "festival_category"
        verbose_name = "Contest Category"
        verbose_name_plural = "Contest Categories"
        unique_together = ("edition", "name")
        ordering = ["edition", "name"]

    def __str__(self) -> str:
        return f"{self.name} - {self.edition.year}"


class Voting(TimeStampedModel):
    """
    Represents an active or scheduled voting process belonging to a specific category.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft / Scheduled"
        OPEN = "OPEN", "Open for Voting"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="votings",
        verbose_name="Contest Category"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Voting Title",
        help_text="Title of the ballot (e.g., 'Elección Popular Rey Vallenato Profesional 2027')."
    )
    description = models.TextField(
        blank=True,
        verbose_name="Instructions / Description",
        help_text="Instructions for voters and details about the voting process."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Voting Status"
    )
    start_datetime = models.DateTimeField(
        verbose_name="Voting Start Time"
    )
    end_datetime = models.DateTimeField(
        verbose_name="Voting End Time"
    )
    max_votes_per_user = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Max Votes Per User",
        help_text="Maximum allowed ballots cast per authenticated user."
    )

    class Meta:
        db_table = "festival_voting"
        verbose_name = "Voting Process"
        verbose_name_plural = "Voting Processes"
        ordering = ["-start_datetime"]

    def __str__(self) -> str:
        return f"{self.title} [{self.get_status_display()}]"

    def clean(self):
        super().clean()
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError({
                "end_datetime": "Voting end timestamp must be strictly after the start timestamp."
            })

    @property
    def is_currently_open(self) -> bool:
        """Determines if the voting is temporally and status-wise available."""
        now = timezone.now()
        return (
            self.status == self.Status.OPEN and
            self.start_datetime <= now <= self.end_datetime
        )


class Option(TimeStampedModel):
    """
    Represents a ballot option / contestant participating in a specific voting process.
    """
    voting = models.ForeignKey(
        Voting,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Voting Process"
    )
    candidate_name = models.CharField(
        max_length=150,
        verbose_name="Candidate / Option Name",
        help_text="Official name of the musical participant or cultural contestant."
    )
    stage_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Artistic / Stage Name",
        help_text="Popular nickname or stage moniker."
    )
    biography = models.TextField(
        blank=True,
        verbose_name="Musical Biography",
        help_text="Artistic trajectory, achievements, and songs/repertoire."
    )
    hometown = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Hometown / Origin",
        help_text="Municipality or region of representation."
    )
    photo_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Photo URL",
        help_text="Public URL of the contestant's profile photograph."
    )
    order_num = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Display Order",
        help_text="Numeric index to order options on the ballot."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active?",
        help_text="Uncheck to disqualify or hide this candidate from the ballot."
    )

    class Meta:
        db_table = "festival_option"
        verbose_name = "Voting Option / Candidate"
        verbose_name_plural = "Voting Options / Candidates"
        unique_together = ("voting", "candidate_name")
        ordering = ["order_num", "candidate_name"]

    def __str__(self) -> str:
        if self.stage_name:
            return f"{self.candidate_name} \"{self.stage_name}\" ({self.voting.category.name})"
        return f"{self.candidate_name} ({self.voting.category.name})"


class Vote(TimeStampedModel):
    """
    Persists an immutable cast ballot by an authenticated voter.
    Prepares the schema for the upcoming phase (Entrega 3) following OCP.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="votes",
        verbose_name="Voter User"
    )
    voting = models.ForeignKey(
        Voting,
        on_delete=models.PROTECT,
        related_name="cast_votes",
        verbose_name="Voting Process"
    )
    selected_option = models.ForeignKey(
        Option,
        on_delete=models.PROTECT,
        related_name="received_votes",
        verbose_name="Selected Candidate / Option"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Voter IP Address"
    )

    class Meta:
        db_table = "festival_vote"
        verbose_name = "Cast Vote"
        verbose_name_plural = "Cast Votes"
        unique_together = ("user", "voting")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Vote by {self.user.username} on {self.voting.title}"

    def clean(self):
        super().clean()
        if self.selected_option.voting_id != self.voting_id:
            raise ValidationError({
                "selected_option": "The selected candidate does not belong to this voting ballot."
            })
