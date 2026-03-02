#!/bin/bash

# Configuration
ENDPOINT="http://localhost:8080/payment"
TOTAL_REQUESTS=5
FROM_USER_ID=1
TO_USER_ID=2
AMOUNT=100

echo "Starting stress test: $TOTAL_REQUESTS requests to $ENDPOINT"
echo "-------------------------------------------------------"

for ((i=1; i<=$TOTAL_REQUESTS; i++))
do
    # Generate a unique Idempotency Key for each loop
    # If 'uuidgen' isn't installed, you can use: IDEM_KEY="key-$RANDOM-$i"
    IDEM_KEY=$(uuidgen)

    echo "[$i/$TOTAL_REQUESTS] Sending request with Key: $IDEM_KEY"

    # curl command
    # -s: Silent mode
    # -X POST: Specify the method
    # -H: Set headers
    # -d: Set the JSON body
    curl -s -X POST "$ENDPOINT" \
         -H "Content-Type: application/json" \
         -H "X-Idempotency-Key: $IDEM_KEY" \
         -d "{
               \"from_user\": \"$FROM_USER_ID\",
               \"to_user\": \"$TO_USER_ID\",
               \"amount\": $AMOUNT,
               \"currency\": \"JPY\"
             }" \
         -w "\nResponse Code: %{http_code}\n\n"

    sleep 1

done

echo "-------------------------------------------------------"
echo "Stress test complete."