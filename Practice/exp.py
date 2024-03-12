from datetime import datetime, timedelta
import calendar
def get_expiry_date(input_date):
  # Convert input date string to datetime object
  date_obj = datetime.strptime(input_date, "%d-%m-%Y").date()

  # Get the weekday (0 - Monday, 6 - Sunday)
  weekday = date_obj.weekday()

  # Calculate days to add to reach the next Thursday (considering potential wrap-around)
  days_to_add = (calendar.THURSDAY - weekday) % 7

  # Add the calculated days to get the expiry date
  expiry_date = date_obj + timedelta(days=days_to_add)

  # Return expiry date in the desired format
  return expiry_date.strftime("%d-%m-%Y")

# Example usage
input_date = "12-03-2024"
expiry_date = get_expiry_date(input_date)

print(f"Expiry Date (First Thursday): {expiry_date}")
