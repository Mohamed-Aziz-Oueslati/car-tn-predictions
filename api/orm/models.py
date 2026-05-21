"""
models.py – SQLAlchemy ORM models for the AutoMarket FastAPI application.

Tables derived from the SQL queries in main.py:
  - users
  - cars
  - car_views
  - conversations
  - messages
  - favorites
  - notifications
  - user_preferences
  - notification_preferences
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class User(Base):
    """
    Registered users.

    Columns discovered from:
      - INSERT INTO users (nom, prenom, email, password_hash, telephone) … RETURNING id, nom, prenom, email, avatar_url
      - SELECT id, nom, prenom, email, telephone, avatar_url, gouvernorat, bio, created_at FROM users
      - UPDATE users SET nom, prenom, telephone, gouvernorat, bio, updated_at, email, password_hash, avatar_url
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identity
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Optional contact / profile
    telephone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    gouvernorat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    cars: Mapped[List["Car"]] = relationship("Car", back_populates="owner", cascade="all, delete-orphan")
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender"
    )
    received_messages: Mapped[List["Message"]] = relationship(
        "Message", foreign_keys="Message.receiver_id", back_populates="receiver"
    )
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[Optional["NotificationPreferences"]] = relationship(
        "NotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ---------------------------------------------------------------------------
# cars
# ---------------------------------------------------------------------------

class Car(Base):
    """
    Car listings (annonces).

    Columns discovered from:
      - INSERT INTO cars (marque, modele, kilometrage, energie, boite_vitesse,
            puissance_fiscale, puissance_ch, carrosserie, gouvernorat,
            couleur_exterieure, couleur_interieure, sellerie,
            nombre_places, nombre_portes, cylindree, age_voiture,
            prix, description, image_url, user_id,
            vendeur_nom, vendeur_telephone, images) … RETURNING id
      - SELECT c.*, … statut, created_at
      - UPDATE cars SET statut = :statut
    """

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Core listing info ────────────────────────────────────────────────────
    marque: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    modele: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Technical specs ──────────────────────────────────────────────────────
    kilometrage: Mapped[float] = mapped_column(Float, nullable=False)
    energie: Mapped[str] = mapped_column(String(50), nullable=False)          # Essence / Diesel / …
    boite_vitesse: Mapped[str] = mapped_column(String(50), nullable=False)    # Manuelle / Automatique
    puissance_fiscale: Mapped[int] = mapped_column(Integer, nullable=False)
    puissance_ch: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    carrosserie: Mapped[str] = mapped_column(String(50), nullable=False)
    couleur_exterieure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    couleur_interieure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sellerie: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nombre_places: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nombre_portes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cylindree: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    age_voiture: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # years since 2026

    # ── Listing metadata ─────────────────────────────────────────────────────
    prix: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gouvernorat: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, server_default="disponible")
    # statut values: 'disponible' | 'vendue'

    # ── Media ────────────────────────────────────────────────────────────────
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    images: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), nullable=True
    )  # stored as PostgreSQL TEXT[]

    # ── Seller snapshot (denormalised for speed) ─────────────────────────────
    vendeur_nom: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vendeur_telephone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ── FK ───────────────────────────────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    owner: Mapped["User"] = relationship("User", back_populates="cars")
    views: Mapped[List["CarView"]] = relationship("CarView", back_populates="car", cascade="all, delete-orphan")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="car", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="car", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Car id={self.id} marque={self.marque!r} statut={self.statut!r}>"


# ---------------------------------------------------------------------------
# car_views
# ---------------------------------------------------------------------------

class CarView(Base):
    """
    Unique page-view tracker for car listings (1 view per IP per hour).

    Columns discovered from:
      - INSERT INTO car_views (car_id, viewer_ip)
      - SELECT id FROM car_views WHERE car_id = :car_id AND viewer_ip = :ip
            AND viewed_at > NOW() - INTERVAL '1 hour'
      - SELECT COUNT(*) FROM car_views cv JOIN cars c ON cv.car_id = c.id
    """

    __tablename__ = "car_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewer_ip: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv4/IPv6
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    car: Mapped["Car"] = relationship("Car", back_populates="views")

    def __repr__(self) -> str:
        return f"<CarView car_id={self.car_id} ip={self.viewer_ip!r}>"


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------

class Conversation(Base):
    """
    One conversation thread = (buyer, seller, car) triple.

    Columns discovered from:
      - SELECT id FROM conversations
            WHERE (user1_id = :u1 AND user2_id = :u2 AND car_id = :car)
               OR (user1_id = :u2 AND user2_id = :u1 AND car_id = :car)
      - INSERT INTO conversations (user1_id, user2_id, car_id) … RETURNING id
      - JOIN users u1 ON c.user1_id = u1.id  /  JOIN users u2 ON c.user2_id = u2.id
      - JOIN cars ca ON c.car_id = ca.id
    """

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", "car_id", name="uq_conversation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user2_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id])
    car: Mapped["Car"] = relationship("Car")

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} car_id={self.car_id}>"


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

class Message(Base):
    """
    Individual chat messages between users about a specific car.

    Columns discovered from:
      - INSERT INTO messages (sender_id, receiver_id, car_id, content)
      - SELECT m.id, m.sender_id, m.receiver_id, m.content, m.is_read, m.created_at, u.prenom AS sender_prenom
      - UPDATE messages SET is_read = TRUE WHERE receiver_id = :uid AND sender_id = :other AND car_id = :car
      - SELECT COUNT(*) FROM messages WHERE receiver_id = :uid AND is_read = FALSE
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    car: Mapped["Car"] = relationship("Car")

    def __repr__(self) -> str:
        return f"<Message id={self.id} sender={self.sender_id} receiver={self.receiver_id} read={self.is_read}>"


# ---------------------------------------------------------------------------
# favorites
# ---------------------------------------------------------------------------

class Favorite(Base):
    """
    User's saved / bookmarked car listings.

    Columns discovered from:
      - INSERT INTO favorites (user_id, car_id)
      - SELECT id FROM favorites WHERE user_id = :uid AND car_id = :car
      - DELETE FROM favorites WHERE user_id = :uid AND car_id = :car
      - SELECT c.* FROM favorites f JOIN cars c ON f.car_id = c.id WHERE f.user_id = :uid
      - SELECT car_id FROM favorites WHERE user_id = :uid
    """

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "car_id", name="uq_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    car: Mapped["Car"] = relationship("Car", back_populates="favorites")

    def __repr__(self) -> str:
        return f"<Favorite user_id={self.user_id} car_id={self.car_id}>"


# ---------------------------------------------------------------------------
# notifications
# ---------------------------------------------------------------------------

class Notification(Base):
    """
    In-app notifications sent when a matching new car is listed.

    Columns discovered from:
      - INSERT INTO notifications (user_id, type, title, body, car_id)
      - SELECT n.id, n.type, n.title, n.body, n.is_read, n.created_at, n.car_id, …
      - UPDATE notifications SET is_read = TRUE WHERE id = :id AND user_id = :uid
      - DELETE FROM notifications WHERE user_id = :uid
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    car_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cars.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g. 'new_car'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    car: Mapped[Optional["Car"]] = relationship("Car", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} type={self.type!r} read={self.is_read}>"


# ---------------------------------------------------------------------------
# user_preferences
# ---------------------------------------------------------------------------

class UserPreferences(Base):
    """
    Search / notification filter preferences (one row per user).

    Columns discovered from:
      - SELECT * FROM user_preferences WHERE user_id = :uid
      - INSERT INTO user_preferences (user_id, marques, carrosseries, energies,
            gouvernorats, budget_min, budget_max, km_max, age_max, notify_enabled)
      - UPDATE user_preferences SET marques, carrosseries, energies, gouvernorats,
            budget_min, budget_max, km_max, age_max, notify_enabled, updated_at
      - Used in create_notifications_new_car: p.marques, p.carrosseries, p.energies,
            p.gouvernorats, p.budget_min, p.budget_max, p.km_max, p.age_max, p.notify_enabled
    """

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Array filters (PostgreSQL TEXT[])
    marques: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    carrosseries: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    energies: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    gouvernorats: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)

    # Numeric filters
    budget_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, server_default="0")
    budget_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, server_default="999999")
    km_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, server_default="999999")
    age_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, server_default="20")

    # Toggle
    notify_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default="true")

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreferences user_id={self.user_id}>"


# ---------------------------------------------------------------------------
# notification_preferences
# ---------------------------------------------------------------------------

class NotificationPreferences(Base):
    """
    Separate notification-specific preferences table (one row per user).

    Columns discovered from:
      - SELECT * FROM notification_preferences WHERE user_id = :uid
      - INSERT INTO notification_preferences (user_id, budget_min, budget_max,
            marques, energies, carrosseries, gouvernorats,
            kilometrage_max, annee_min, notifications_actives)
      - UPDATE notification_preferences SET budget_min, budget_max, marques, energies,
            carrosseries, gouvernorats, kilometrage_max, annee_min,
            notifications_actives, updated_at
    """

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Budget range
    budget_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, server_default="0")
    budget_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, server_default="9999999")

    # Array filters (PostgreSQL TEXT[])
    marques: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    energies: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    carrosseries: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    gouvernorats: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)

    # Other numeric filters
    kilometrage_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, server_default="999999")
    annee_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, server_default="0")

    # Toggle
    notifications_actives: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, server_default="true"
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")

    def __repr__(self) -> str:
        return f"<NotificationPreferences user_id={self.user_id}>"