CREATE TABLE IF NOT EXISTS carbookings
(
    carbookingid uuid NOT NULL DEFAULT gen_random_uuid(),
    userid uuid NOT NULL,
    bookingreference varchar(255) NOT NULL,
    bookingdate timestamp  NOT NULL,
    bookingdetails jsonb,
    paymentid varchar(255),
    insuranceamount numeric NOT NULL,
    insurancetype varchar(225),
    totalamount numeric NOT NULL,
    created_at timestamp  NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now(),
    trip_id uuid,
    CONSTRAINT carbookings_pkey 
    PRIMARY KEY (carbookingid)
    
)


select * from carbookings

-- drop table carbookings;


select * from user_bookings