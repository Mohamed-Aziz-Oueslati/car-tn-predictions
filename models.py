"""
models.py — SQLAlchemy ORM models for the AutoMarket Car Price Prediction API.
Derived from main.py SQL queries and table references.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


# ─── Base ─────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ─── Users ────────────────────────────────────────────────────────────


class User(Base):
    """
    Registered users of the platform.

    Referenced by:
        cars.user_id, messages.sender_id / receiver_id,
        conversations.user1_id / user2_id, favorites.user_id,
        notifications.user_id, user_preferences.user_id,
        notification_preferences.user_id
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telephone = Column(String(30), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    gouvernorat = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    cars = relationship("Car", back_populates="owner", foreign_keys="Car.user_id")
    sent_messages = relationship(
        "Message", back_populates="sender", foreign_keys="Message.sender_id"
    )
    received_messages = relationship(
        "Message", back_populates="receiver", foreign_keys="Message.receiver_id"
    )
    conversations_as_user1 = relationship(
        "Conversation", back_populates="user1", foreign_keys="Conversation.user1_id"
    )
    conversations_as_user2 = relationship(
        "Conversation", back_populates="user2", foreign_keys="Conversation.user2_id"
    )
    favorites = relationship("Favorite", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    preferences = relationship(
        "UserPreference", back_populates="user", uselist=False
    )
    notification_preferences = relationship(
        "NotificationPreference", back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ─── Cars ─────────────────────────────────────────────────────────────


class Car(Base):
    """
    Car listings (annonces) posted by users.

    ``images`` stores a JSON array of image URLs.
    ``statut`` is either 'disponible' or 'vendue'.
    """

    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # ── Identification ─────────────────────────────────────────────────
    marque = Column(String(100), nullable=False, index=True)
    modele = Column(String(150), nullable=True)

    # ── Technical specs ────────────────────────────────────────────────
    kilometrage = Column(Float, nullable=False)
    energie = Column(String(50), nullable=True)           # Essence / Diesel / Electrique / Hybride / GPL
    boite_vitesse = Column(String(50), nullable=True)     # Manuelle / Automatique
    puissance_fiscale = Column(Integer, nullable=True)
    puissance_ch = Column(Integer, nullable=True)
    carrosserie = Column(String(50), nullable=True)       # Berline / SUV / …
    couleur_exterieure = Column(String(80), nullable=True)
    couleur_interieure = Column(String(80), nullable=True)
    sellerie = Column(String(80), nullable=True)
    nombre_places = Column(Integer, nullable=True)
    nombre_portes = Column(Integer, nullable=True)
    cylindree = Column(Float, nullable=True)
    age_voiture = Column(Integer, nullable=True)          # 2026 - année de mise en circulation

    # ── Listing info ───────────────────────────────────────────────────
    gouvernorat = Column(String(100), nullable=True, index=True)
    prix = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    statut = Column(String(20), nullable=True, default="disponible")  # disponible | vendue

    # ── Seller snapshot (denormalised for convenience) ─────────────────
    vendeur_nom = Column(String(200), nullable=True)
    vendeur_telephone = Column(String(30), nullable=True)

    # ── Media ──────────────────────────────────────────────────────────
    image_url = Column(String(512), nullable=True)
    images = Column(JSONB, nullable=True)   # list[str] — JSON array of image URLs

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    owner = relationship("User", back_populates="cars", foreign_keys=[user_id])
    messages = relationship("Message", back_populates="car")
    conversations = relationship("Conversation", back_populates="car")
    favorites = relationship("Favorite", back_populates="car")
    notifications = relationship("Notification", back_populates="car")
    views = relationship("CarView", back_populates="car")

    def __repr__(self) -> str:
        return f"<Car id={self.id} {self.marque} {self.modele} statut={self.statut!r}>"


# ─── Car Views ────────────────────────────────────────────────────────


class CarView(Base):
    """
    Tracks unique page views per IP per car (deduplicated within 1 hour).
    Used for dashboard analytics.
    """

    __tablename__ = "car_views"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    viewer_ip = Column(String(45), nullable=False)   # IPv4 or IPv6
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────
    car = relationship("Car", back_populates="views")

    def __repr__(self) -> str:
        return f"<CarView car_id={self.car_id} ip={self.viewer_ip!r}>"


# ─── Conversations ────────────────────────────────────────────────────


class Conversation(Base):
    """
    A unique thread between two users about a specific car listing.
    The (user1_id, user2_id, car_id) triplet is effectively unique,
    but the query checks both orderings so no DB-level unique constraint
    is strictly required (though it is recommended).
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────
    user1 = relationship("User", back_populates="conversations_as_user1", foreign_keys=[user1_id])
    user2 = relationship("User", back_populates="conversations_as_user2", foreign_keys=[user2_id])
    car = relationship("Car", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} users=({self.user1_id},{self.user2_id}) car={self.car_id}>"


# ─── Messages ─────────────────────────────────────────────────────────


class Message(Base):
    """
    Individual chat messages between a buyer and a seller about a car.
    ``is_read`` is set to TRUE when the receiver fetches the thread.
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])
    car = relationship("Car", back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} from={self.sender_id} to={self.receiver_id} "
            f"car={self.car_id} read={self.is_read}>"
        )


# ─── Favorites ────────────────────────────────────────────────────────


class Favorite(Base):
    """
    User's saved / bookmarked car listings.
    The (user_id, car_id) pair is logically unique.
    """

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id = Column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────
    user = relationship("User", back_populates="favorites")
    car = relationship("Car", back_populates="favorites")

    def __repr__(self) -> str:
        return f"<Favorite user={self.user_id} car={self.car_id}>"


# ─── Notifications ────────────────────────────────────────────────────


class Notification(Base):
    """
    In-app notifications pushed to users when a new car matching their
    preferences is listed.

    ``type`` is currently always 'new_car' but is kept generic.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="new_car")
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    car_id = Column(Integer, ForeignKey("cars.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────
    user = relationship("User", back_populates="notifications")
    car = relationship("Car", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user={self.user_id} type={self.type!r} read={self.is_read}>"


# ─── User Preferences ─────────────────────────────────────────────────


class UserPreference(Base):
    """
    Per-user search / notification filter preferences.

    Array columns (``marques``, ``carrosseries``, ``energies``,
    ``gouvernorats``) use PostgreSQL native ARRAY(String) so they can
    be compared with ``ANY``/``@>`` operators or Python list equality.
    ``notify_enabled`` gates all push notifications for this user.
    """

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    marques = Column(ARRAY(String), nullable=True, default=list)
    carrosseries = Column(ARRAY(String), nullable=True, default=list)
    energies = Column(ARRAY(String), nullable=True, default=list)
    gouvernorats = Column(ARRAY(String), nullable=True, default=list)

    budget_min = Column(Float, nullable=True, default=0.0)
    budget_max = Column(Float, nullable=True, default=999999.0)
    km_max = Column(Float, nullable=True, default=999999.0)
    age_max = Column(Integer, nullable=True, default=20)

    notify_enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreference user={self.user_id} notify={self.notify_enabled}>"


# ─── Notification Preferences ─────────────────────────────────────────


class NotificationPreference(Base):
    """
    Extended notification filter settings (separate from UserPreference).

    Provides finer-grained control: ``annee_min`` (min manufacture year),
    ``kilometrage_max``, and a global ``notifications_actives`` toggle.
    """

    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    budget_min = Column(Float, nullable=True, default=0.0)
    budget_max = Column(Float, nullable=True, default=9999999.0)
    marques = Column(ARRAY(String), nullable=True, default=list)
    energies = Column(ARRAY(String), nullable=True, default=list)
    carrosseries = Column(ARRAY(String), nullable=True, default=list)
    gouvernorats = Column(ARRAY(String), nullable=True, default=list)
    kilometrage_max = Column(Float, nullable=True, default=999999.0)
    annee_min = Column(Integer, nullable=True, default=0)
    notifications_actives = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self) -> str:
        return (
            f"<NotificationPreference user={self.user_id} "
            f"active={self.notifications_actives}>"
        )