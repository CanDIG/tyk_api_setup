{
    "${TYK_POLICY_ID}": {
        "access_rights": {
            "${CANDIG_API_ID}": {
                "allowed_urls": [],
                "api_id": "${CANDIG_API_ID}",
                "api_name": "${CANDIG_API_NAME}",
                "versions": [
                    "Default"
                ]
            }
        },        
        "active": true,
        "name": "CanDIG Policy",
        "rate": 100,
        "per": 1,
        "quota_max": 10000,
        "quota_renewal_rate": 3600,
        "tags": ["Startup Users"]
    }
}