"User": {
    "_id": "ObjectId",
    "name": "string",
    "email": "string",                   // Indexed for login and lookup
    "favorites": ["ObjectId"],           // References to PaperSummary _id
    "created_at": "Date",
    "updated_at": "Date"
},

"PaperSummary": {
    "_id": "ObjectId",
    "user_id": "ObjectId",               // Owner reference; index this field for user queries
    "title": "string",
    "authors": [{
        "name": "string",
        "affiliation": "string"
        "email": "string"
    }],
    "date_published": "Date",
    "metadata": {
      "doi": "string",                   // Unique identifier; indexed for deduplication
      "conference": "string",
      "tags": ["string"]
    },
    "summary": {
	  "research_problem": "string",
      "objective": "string",            // Quick overview, can be used in previews
      "key_findings": "string",
      "methods": "string",
      "numbers": "string",
      "dataset": "string",
      "baseline_comparisons": "string",
      "limitations": "string",
      "future_work": "string",
      "novelty_statement": "string",       // How the paper advances the field (what's new?)
      "user_given_fileds": [{
        "filed_name": "string",
        "value": "string"
      }]
    },
    "references": ["String"],
    "image_cdns": ["string"],            // Up until this getting from gemini
    "created_at": "Date",
    "updated_at": "Date"
  },
