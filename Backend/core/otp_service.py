"""
Redis-based OTP service for memory-efficient OTP management
"""
from django.core.cache import cache
from django.utils import timezone
import random
import logging

logger = logging.getLogger(__name__)


class OTPService:
    """
    Redis-based OTP service that doesn't store OTPs in the database
    """
    
    OTP_EXPIRY_MINUTES = 15
    MAX_ATTEMPTS_PER_HOUR = 5
    MAX_OTP_SENDS_PER_HOUR = 3
    
    @staticmethod
    def _get_otp_key(identifier):
        """Get Redis key for OTP storage"""
        return f"otp:{identifier}"
    
    @staticmethod
    def _get_attempts_key(identifier):
        """Get Redis key for attempt tracking"""
        return f"otp_attempts:{identifier}"
    
    @staticmethod
    def _get_throttle_key(identifier):
        """Get Redis key for send throttling"""
        return f"otp_throttle:{identifier}"
    
    @classmethod
    def generate_otp(cls, identifier):
        """
        Generate a 6-digit OTP and store in Redis
        
        Args:
            identifier: Unique identifier (user_id, phone, email)
        
        Returns:
            str: Generated OTP
        """
        otp = ''.join(random.choices('0123456789', k=6))
        key = cls._get_otp_key(identifier)
        
        # Store in Redis with expiry
        cache.set(key, otp, timeout=cls.OTP_EXPIRY_MINUTES * 60)
        
        logger.info(f"🔐 Generated OTP for {identifier} (expires in {cls.OTP_EXPIRY_MINUTES} minutes)")
        return otp
    
    @classmethod
    def verify_otp(cls, identifier, otp):
        """
        Verify OTP from Redis
        
        Args:
            identifier: Unique identifier (user_id, phone, email)
            otp: OTP to verify
        
        Returns:
            tuple: (bool: is_valid, str: message)
        """
        # Check if too many failed attempts
        if not cls._check_attempts(identifier):
            logger.warning(f"❌ Too many OTP attempts for {identifier}")
            return False, "Too many failed attempts. Please try again later."
        
        key = cls._get_otp_key(identifier)
        stored_otp = cache.get(key)
        
        if stored_otp is None:
            logger.warning(f"❌ OTP expired or not found for {identifier}")
            cls._record_attempt(identifier, False)
            return False, "OTP has expired or is invalid"
        
        if stored_otp != otp:
            logger.warning(f"❌ Invalid OTP for {identifier}")
            cls._record_attempt(identifier, False)
            return False, "Invalid OTP"
        
        # OTP is valid - delete it and clear attempts
        cache.delete(key)
        cls._clear_attempts(identifier)
        
        logger.info(f"✅ OTP verified successfully for {identifier}")
        return True, "OTP verified successfully"
    
    @classmethod
    def can_send_otp(cls, identifier):
        """
        Check if we can send a new OTP (throttling)
        
        Args:
            identifier: Unique identifier (phone, email)
        
        Returns:
            tuple: (bool: can_send, str: message)
        """
        throttle_key = cls._get_throttle_key(identifier)
        send_count = cache.get(throttle_key, 0)
        
        if send_count >= cls.MAX_OTP_SENDS_PER_HOUR:
            logger.warning(f"❌ OTP send limit reached for {identifier}")
            return False, f"Too many OTP requests. Please try again later."
        
        # Increment counter (expires in 1 hour)
        cache.set(throttle_key, send_count + 1, timeout=3600)
        
        return True, "OK"
    
    @classmethod
    def _check_attempts(cls, identifier):
        """Check if user hasn't exceeded max attempts"""
        attempts_key = cls._get_attempts_key(identifier)
        attempts = cache.get(attempts_key, 0)
        return attempts < cls.MAX_ATTEMPTS_PER_HOUR
    
    @classmethod
    def _record_attempt(cls, identifier, successful):
        """Record an OTP verification attempt"""
        if not successful:
            attempts_key = cls._get_attempts_key(identifier)
            attempts = cache.get(attempts_key, 0)
            # Store for 1 hour
            cache.set(attempts_key, attempts + 1, timeout=3600)
    
    @classmethod
    def _clear_attempts(cls, identifier):
        """Clear attempt counter after successful verification"""
        attempts_key = cls._get_attempts_key(identifier)
        cache.delete(attempts_key)
    
    @classmethod
    def get_remaining_time(cls, identifier):
        """
        Get remaining time for OTP validity
        
        Returns:
            int: Remaining seconds, or None if OTP doesn't exist
        """
        key = cls._get_otp_key(identifier)
        ttl = cache.ttl(key) if hasattr(cache, 'ttl') else None
        return ttl
    
    @classmethod
    def invalidate_otp(cls, identifier):
        """Manually invalidate an OTP"""
        key = cls._get_otp_key(identifier)
        cache.delete(key)
        logger.info(f"🗑️ OTP invalidated for {identifier}")
