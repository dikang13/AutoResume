"""User profile management for persistent memory across sessions."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile containing experience, skills, and preferences."""

    user_id: str = Field(description="Unique identifier for the user")
    name: str = Field(default="", description="User's name")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Experience and skills
    experiences: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of work experiences with details"
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Technical and soft skills"
    )
    projects: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Notable projects"
    )
    education: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Educational background"
    )

    # Preferences
    preferences: Dict[str, str] = Field(
        default_factory=dict,
        description="User preferences for resume style, etc."
    )

    # Notes from conversations
    notes: List[str] = Field(
        default_factory=list,
        description="Notes from past conversations"
    )

    # Resume file path for identity verification
    resume_files: List[str] = Field(
        default_factory=list,
        description="Paths to resume files associated with this user"
    )


class UserProfileManager:
    """Manages user profiles and persistent memory."""

    def __init__(self, profiles_dir: str = ".user_profiles"):
        """
        Initialize the profile manager.

        Args:
            profiles_dir: Directory to store user profiles
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)

    def _get_profile_path(self, user_id: str) -> Path:
        """Get the file path for a user's profile."""
        safe_id = user_id.replace("/", "_").replace("\\", "_")
        return self.profiles_dir / f"{safe_id}.json"

    def profile_exists(self, user_id: str) -> bool:
        """Check if a profile exists for the given user ID."""
        return self._get_profile_path(user_id).exists()

    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Load a user profile.

        Args:
            user_id: The user's unique identifier

        Returns:
            UserProfile if exists, None otherwise
        """
        profile_path = self._get_profile_path(user_id)

        if not profile_path.exists():
            return None

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return UserProfile(**data)
        except Exception as e:
            print(f"Warning: Failed to load profile {user_id}: {e}")
            return None

    def save_profile(self, profile: UserProfile) -> None:
        """
        Save a user profile.

        Args:
            profile: The UserProfile to save
        """
        profile.updated_at = datetime.now().isoformat()
        profile_path = self._get_profile_path(profile.user_id)

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(), f, indent=2)

    def create_profile(
        self,
        user_id: str,
        name: str = "",
        resume_path: str = ""
    ) -> UserProfile:
        """
        Create a new user profile.

        Args:
            user_id: Unique identifier for the user
            name: User's name
            resume_path: Path to the user's resume file

        Returns:
            The newly created UserProfile
        """
        profile = UserProfile(
            user_id=user_id,
            name=name,
            resume_files=[resume_path] if resume_path else []
        )

        self.save_profile(profile)
        return profile

    def update_from_conversation(
        self,
        user_id: str,
        experiences: Optional[List[Dict[str, str]]] = None,
        skills: Optional[List[str]] = None,
        notes: Optional[List[str]] = None
    ) -> None:
        """
        Update a user profile from conversation data.

        Args:
            user_id: The user's unique identifier
            experiences: New experiences to add
            skills: New skills to add
            notes: New notes to add
        """
        profile = self.load_profile(user_id)

        if profile is None:
            profile = self.create_profile(user_id)

        if experiences:
            for exp in experiences:
                if exp not in profile.experiences:
                    profile.experiences.append(exp)

        if skills:
            for skill in skills:
                if skill not in profile.skills:
                    profile.skills.append(skill)

        if notes:
            for note in notes:
                if note not in profile.notes:
                    profile.notes.append(note)

        self.save_profile(profile)

    def find_profile_by_resume(self, resume_path: str) -> Optional[UserProfile]:
        """
        Find a user profile by resume file path.

        Args:
            resume_path: Path to the resume file

        Returns:
            UserProfile if found, None otherwise
        """
        # Normalize path for comparison
        resume_path = str(Path(resume_path).resolve())

        # Check all existing profiles
        for profile_file in self.profiles_dir.glob("*.json"):
            profile = self.load_profile(profile_file.stem)
            if profile:
                # Check if any of the resume files match
                for saved_path in profile.resume_files:
                    if str(Path(saved_path).resolve()) == resume_path:
                        return profile

        return None

    def list_profiles(self) -> List[UserProfile]:
        """
        List all user profiles.

        Returns:
            List of all UserProfiles
        """
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            profile = self.load_profile(profile_file.stem)
            if profile:
                profiles.append(profile)

        return profiles
