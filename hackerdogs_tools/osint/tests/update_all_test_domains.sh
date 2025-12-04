#!/bin/bash
# Script to update all test files to use random domains
# This replaces example.com with get_random_domain() calls

echo "Updating test files to use random domains..."
echo "=============================================="

# List of test files that need updating (excluding test_utils.py and already updated ones)
TEST_FILES=(
    "test_nuclei.py"
    "test_dnsdumpster.py"
    "test_theharvester.py"
    "test_ghunt.py"
    "test_holehe.py"
    "test_scrapy.py"
    "test_waybackurls.py"
    "test_spiderfoot.py"
    "test_urlhaus.py"
    "test_otx.py"
    "test_misp.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Processing $file..."
        
        # Add import if not present
        if ! grep -q "from hackerdogs_tools.osint.test_domains import" "$file"; then
            sed -i '' '/from hackerdogs_tools.osint.tests.test_utils import/a\
from hackerdogs_tools.osint.test_domains import get_random_domain
' "$file"
        fi
        
        # Replace domain="example.com" with domain=get_random_domain()
        sed -i '' 's/domain="example\.com"/domain=get_random_domain()/g' "$file"
        
        # Replace url="https://example.com" with url=f"https://{get_random_domain()}"
        sed -i '' 's/url="https:\/\/example\.com"/url=f"https:\/\/{get_random_domain()}"/g' "$file"
        
        # Replace target="https://example.com" with target=f"https://{get_random_domain()}"
        sed -i '' 's/target="https:\/\/example\.com"/target=f"https:\/\/{get_random_domain()}"/g' "$file"
        
        # Replace email="test@example.com" with email=f"test@{get_random_domain()}"
        sed -i '' 's/email="test@example\.com"/email=f"test@{get_random_domain()}"/g' "$file"
        
        # Replace example.com in messages (need to add test_domain variable first)
        # This is more complex and may need manual review
        
        echo "✅ Updated $file"
    else
        echo "⚠️  $file not found"
    fi
done

echo ""
echo "=============================================="
echo "Update complete!"
echo ""
echo "Note: Some files may need manual review for:"
echo "  - Messages with example.com"
echo "  - Task descriptions with example.com"
echo "  - Complex string formatting"

