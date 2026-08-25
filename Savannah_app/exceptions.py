class BookingError(Exception):
    """Base exception for booking-related business errors."""


class InvalidBookingError(BookingError):
    """The requested booking data is invalid."""


class SlotUnavailableError(BookingError):
    """The requested appointment slot is not available."""


class AppointmentCancelledError(BookingError):
    """The appointment has already been cancelled."""


class ConflictError(BookingError):
    """The operation conflicts with the current database state."""
