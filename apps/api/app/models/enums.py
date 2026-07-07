from enum import StrEnum

class BusinessStatus(StrEnum):
    PENDING_KYB = 'pending_kyb'
    VERIFIED = 'verified'
    SUSPENDED = 'suspended'

class OrderStatus(StrEnum):
    DRAFT = 'draft'
    CONFIRMED = 'confirmed'
    IN_FULFILMENT = 'in_fulfilment'
    DELIVERED = 'delivered'
    DISPUTED = 'disputed'
    CLOSED = 'closed'

class InvoiceStatus(StrEnum):
    ISSUED = 'issued'
    BUYER_CONFIRMED = 'buyer_confirmed'
    DISPUTED = 'disputed'
    PAID = 'paid'
    CANCELLED = 'cancelled'

class ProofStatus(StrEnum):
    SUBMITTED = 'submitted'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    ANCHORED = 'anchored'

class ReceivableStatus(StrEnum):
    CREATED = 'created'
    TOKENIZED = 'tokenized'
    FINANCED = 'financed'
    SETTLED = 'settled'
    DEFAULTED = 'defaulted'
    CANCELLED = 'cancelled'

class SmartLCStatus(StrEnum):
    CREATED = 'created'
    FUNDED = 'funded'
    LOCKED = 'locked'
    RELEASED = 'released'
    REFUNDED = 'refunded'
    DISPUTED = 'disputed'

class OutboxStatus(StrEnum):
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'

class KYBStatus(StrEnum):
    NOT_STARTED = 'not_started'
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    PENDING_REVIEW = 'pending_review'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    NEEDS_MORE_INFO = 'needs_more_info'
    MANUAL_REVIEW = 'manual_review'
    EXPIRED = 'expired'
    SUSPENDED = 'suspended'

class KYBRiskLevel(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
