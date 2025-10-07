go to .env file and replace with your environment variable before building the image 

to build the image  

docker build -t IMAGE_NAME .

to run the container 

docker run -e MEETING_ID=your_meeting_id -e NAME=your_name -e DURATION=30 -e UUID=unique_identifier YOUR_IMAGE_NAME


out of this flags only -

MEETING_ID and UUID is mandatory and other is optional


docker build -t google_meet_bot_image_v1 .