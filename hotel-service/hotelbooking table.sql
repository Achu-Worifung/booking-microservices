CREATE TABLE IF NOT EXISTS hotelbookings
(
    hotelbookingid uuid NOT NULL DEFAULT gen_random_uuid(),
    userid uuid NOT NULL,
    bookingreference varchar(255) NOT NULL,
    bookingdate timestamp  NOT NULL,
    bookingdetails jsonb,
    paymentid varchar(255),
    totalamount numeric NOT NULL,
    created_at timestamp  NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now(),
    trip_id uuid,
    CONSTRAINT hotelbookings_pkey 
    PRIMARY KEY (hotelbookingid)
    
);


select * from hotelbookings;

drop table hotelbookings;


create database hotel_db;

select * from trips